import pandas as pd
import numpy as np
import traceback
import datetime
import logging
import tqdm
import uuid
import os

from .. import entities
from . import BaseModelAdapter, metrics

logger = logging.getLogger(name='dtlpy')


# Utility functions to use in the model adapters
#   these wrapper function should ease to make sure all predictions are built with proper metadata structure

def mean_or_nan(arr):
    if isinstance(arr, list) and len(arr) == 0:
        return np.nan
    else:
        return np.mean(arr)


def create_collection():
    collection = entities.AnnotationCollection(item=None)
    return collection


def model_info_name(model: entities.Model, snapshot: entities.Snapshot):
    if snapshot is None:
        return "{}-no-snapshot".format(model.name)
    else:
        return "{}-{}".format(model.name, snapshot.name)


def add_box_prediction(left, top, right, bottom, label, score,
                       adapter: BaseModelAdapter = None,
                       model: entities.Model = None, snapshot: entities.Snapshot = None,
                       collection: entities.AnnotationCollection = None):
    if collection is None:
        collection = create_collection()

    if adapter is not None:
        model = adapter.model_entity
        snapshot = adapter.snapshot

    model_snap_name = model_info_name(model=model, snapshot=snapshot)
    collection.add(
        annotation_definition=entities.Box(
            left=float(left),
            top=float(top),
            right=float(right),
            bottom=float(bottom),
            label=str(label)
        ),
        model_info={
            'name': model_snap_name,
            'confidence': float(score),
            'model_id': model.id,
            'snapshot_id': snapshot.id
        }
    )
    return collection


def add_classification(label, score,
                       adapter: BaseModelAdapter = None,
                       model: entities.Model = None, snapshot: entities.Snapshot = None,
                       collection: entities.AnnotationCollection = None):
    if collection is None:
        collection = create_collection()

    if adapter is not None:
        model = adapter.model_entity
        snapshot = adapter.snapshot

    model_snap_name = model_info_name(model=model, snapshot=snapshot)
    collection.add(annotation_definition=entities.Classification(label=label),
                   model_info={
                       'name': model_snap_name,
                       'confidence': float(score),
                       'model_id': model.id,
                       'snapshot_id': snapshot.id
                   })
    return collection


def is_ann_pred(ann: entities.Annotation, model: entities.Model = None, snapshot: entities.Snapshot = None,
                verbose=False):
    is_pred = 'user' in ann.metadata and 'model_info' in ann.metadata['user']

    if is_pred and model is not None:
        is_pred = is_pred and model.id == ann.metadata['user']['model_info']['model_id']
        verbose and print("Annotation {!r} prediction with model mismatch".format(ann.id))

    if is_pred and snapshot is not None:
        is_pred = is_pred and snapshot.id == ann.metadata['user']['model_info']['snapshot_id']
        verbose and print("Annotation {!r} prediction with snapshot mismatch".format(ann.id))

    return is_pred


def measure_item_box_predictions(item: entities.Item, model: entities.Model = None, snapshot: entities.Snapshot = None):
    annotations = item.annotations.list(
        filters=entities.Filters(field='type', values='box', resource=entities.FiltersResource.ANNOTATION))
    actuals = [ann for ann in annotations if 'model_info' not in ann.metadata['user']]
    predictions = [ann for ann in annotations if is_ann_pred(ann, model=model, snapshot=snapshot)]

    r_boxes, t_boxes = actuals, predictions  # TODO: test if we need to change the order of ref /test

    box_scores = metrics.match_box(ref_annotations=r_boxes,
                                   test_annotations=t_boxes,
                                   geometry_only=True)
    # Create the symmetric IoU metric
    test_iou_scores = [match.annotation_score for match in box_scores.values() if match.annotation_score > 0]
    matched_box = int(np.sum([1 for score in test_iou_scores if score > 0]))  # len(test_iou_scores)
    total_box = len(r_boxes) + len(t_boxes)
    extra_box = len(t_boxes) - matched_box
    missing_box = len(r_boxes) - matched_box
    assert total_box == extra_box + 2 * matched_box + missing_box
    # add missing to score
    test_iou_scores += [0 for _ in range(missing_box)]
    test_iou_scores += [0 for _ in range(extra_box)]

    boxes_report = {'box_ious': box_scores,
                    'box_annotations': r_boxes,
                    'box_mean_iou': mean_or_nan(test_iou_scores),
                    'box_attributes_scores': mean_or_nan([match.attributes_score for match in box_scores.values()]),
                    'box_ref_number': len(r_boxes),
                    'box_test_number': len(t_boxes),
                    'box_missing': missing_box,
                    'box_total': total_box,
                    'box_matched': matched_box,
                    'box_extra': extra_box,
                    }

    return boxes_report


def measure_annotations(
        annotations_set_one: entities.AnnotationCollection,
        annotations_set_two: entities.AnnotationCollection,
        match_threshold=0.5,
        geometry_only=False,
        compare_types=None):
    """
    Compares list (or collections) of annotations

    :param annotations_set_one: dl.AnnotationCollection entity with a list of annotations to compare
    :param annotations_set_two: dl.AnnotationCollection entity with a list of annotations to compare
    :param match_threshold: IoU threshold to count as a match
    :param geometry_only: ignore label when comparing - measure only geometry
    :param compare_types: list of type to compare. enum dl.AnnotationType

    Returns a dictionary of all the compare data
    """

    if compare_types is None:
        compare_types = [entities.AnnotationType.BOX,
                         entities.AnnotationType.CLASSIFICATION,
                         entities.AnnotationType.POLYGON,
                         entities.AnnotationType.POINT,
                         entities.AnnotationType.SEGMENTATION]
    final_results = dict()
    all_scores = list()

    # for local annotations - set random id if None
    for annotation in annotations_set_one:
        if annotation.id is None:
            annotation.id = str(uuid.uuid1())
    for annotation in annotations_set_two:
        if annotation.id is None:
            annotation.id = str(uuid.uuid1())

    # start comparing
    for compare_type in compare_types:
        matches = metrics.Matches()
        annotation_subset_one = [a for a in annotations_set_one if
                                 a.type == compare_type and not a.metadata.get('system', dict()).get('system', False)]
        annotation_subset_two = [a for a in annotations_set_two if
                                 a.type == compare_type and not a.metadata.get('system', dict()).get('system', False)]
        # create 2d dataframe with annotation id as names and set all to -1 -> not calculated
        if geometry_only:
            matches = metrics.Matchers.general_match(matches=matches,
                                                     first_set=annotation_subset_one,
                                                     second_set=annotation_subset_two,
                                                     match_type=compare_type,
                                                     match_threshold=match_threshold)
        else:
            unique_labels = np.unique([a.label for a in annotation_subset_one] +
                                      [a.label for a in annotation_subset_two])
            for label in unique_labels:
                first_set = [a for a in annotation_subset_one if a.label == label]
                second_set = [a for a in annotation_subset_two if a.label == label]
                matches = metrics.Matchers.general_match(matches=matches,
                                                         first_set=first_set,
                                                         second_set=second_set,
                                                         match_type=compare_type,
                                                         match_threshold=match_threshold)
        if len(matches) == 0:
            continue
        all_scores.extend(matches.to_df()['annotation_score'])
        final_results[compare_type] = metrics.Results(matches=matches,
                                                      annotation_type=compare_type)
    final_results['total_mean_score'] = mean_or_nan(all_scores)
    return final_results


def measure_item(ref_item: entities.Item,
                 test_item: entities.Item,
                 ref_project: entities.Project = None,
                 test_project: entities.Project = None,
                 pbar=None):
    try:
        annotations_set_one = ref_item.annotations.list()
        annotations_set_two = test_item.annotations.list()
        final = measure_annotations(annotations_set_one=annotations_set_one,
                                    annotations_set_two=annotations_set_two)

        # get times
        try:
            ref_item_duration_s = metrics.item_annotation_duration(item=ref_item, project=ref_project)
            ref_item_duration = str(datetime.timedelta(seconds=int(np.round(ref_item_duration_s))))
        except Exception:
            ref_item_duration_s = -1
            ref_item_duration = ''

        try:
            test_item_duration_s = metrics.item_annotation_duration(item=test_item, project=test_project)
            test_item_duration = str(datetime.timedelta(seconds=int(np.round(test_item_duration_s))))
        except Exception:
            test_item_duration_s = -1
            test_item_duration = ''

        final.update({'ref_url': ref_item.platform_url,
                      'test_url': test_item.platform_url,
                      'filename': ref_item.filename,
                      'ref_item_duration[s]': ref_item_duration_s,
                      'test_item_duration[s]': test_item_duration_s,
                      'diff_duration[s]': test_item_duration_s - ref_item_duration_s,
                      # round to sec
                      'ref_item_duration': ref_item_duration,
                      'test_item_duration': test_item_duration,
                      })

        return True, final
    except Exception:
        fail_msg = 'failed measuring. ref_item: {!r}, test_item: {!r}'.format(ref_item.id, test_item.id)
        return False, '{}\n{}'.format(fail_msg, traceback.format_exc())
    finally:
        if pbar is not None:
            pbar.update()


def measure_items(ref_items, ref_project, ref_dataset, ref_name,
                  test_items, test_project, test_dataset, test_name,
                  dump_path=None):
    from multiprocessing.pool import ThreadPool
    ref_items_filepath_dict = {item.filename: item for page in ref_items for item in page}
    test_items_filepath_dict = {item.filename: item for page in test_items for item in page}
    pool = ThreadPool(processes=32)
    pbar = tqdm.tqdm(total=len(ref_items_filepath_dict))
    jobs = dict()
    for filepath, ref_item in ref_items_filepath_dict.items():
        if filepath in test_items_filepath_dict:
            test_item = test_items_filepath_dict[filepath]
            jobs[ref_item.filename] = pool.apply_async(measure_item, kwds={'test_item': test_item,
                                                                           'ref_item': ref_item,
                                                                           'ref_project': ref_project,
                                                                           'test_project': test_project,
                                                                           'pbar': pbar})
    pool.close()
    pool.join()
    _ = [job.wait() for job in jobs.values()]
    raw_items_summary = dict()
    failed_items_errors = dict()
    for filename, job in jobs.items():
        success, result = job.get()
        if success:
            raw_items_summary[filename] = result
        else:
            failed_items_errors[filename] = result
    pool.terminate()
    pbar.close()

    #
    summary = list()
    ref_column_name = 'Ref-{!r}'.format(ref_name)
    test_column_name = 'Test-{!r}'.format(test_name)
    for filename, scores in raw_items_summary.items():
        line = {'filename': scores['filename'],
                ref_column_name: scores['ref_url'],
                test_column_name: scores['test_url'],
                'total_score': scores['total_mean_score'],
                'ref_duration[s]': scores['ref_item_duration[s]'],
                'test_duration[s]': scores['test_item_duration[s]'],
                'diff_duration[s]': scores['diff_duration[s]']}
        for tool_type in list(entities.AnnotationType):
            if tool_type in scores:
                res = scores[tool_type].summary()
                line['{}_annotation_score'.format(tool_type)] = res['mean_annotations_scores']
                line['{}_attributes_score'.format(tool_type)] = res['mean_attributes_scores']
                line['{}_ref_number'.format(tool_type)] = res['n_annotations_set_one']
                line['{}_test_number'.format(tool_type)] = res['n_annotations_set_two']
                line['{}_match_number'.format(tool_type)] = res['n_annotations_matched_total']
        summary.append(line)
    df = pd.DataFrame(summary)
    # Drop column only if all the values are None
    df = df.dropna(how='all', axis=1)
    ####
    if dump_path is not None:
        save_to_file(dump_path=dump_path,
                     df=df,
                     ref_name=ref_name,
                     test_name=test_name)
    return df, raw_items_summary, failed_items_errors


def save_to_file(df, dump_path, ref_name, test_name):
    # df = df.sort_values(by='box_score')
    ref_column_name = 'Ref-{!r}'.format(ref_name)
    test_column_name = 'Test-{!r}'.format(test_name)

    def make_clickable(val):
        return '<a href="{}">{}</a>'.format(val, 'item')

    s = df.style.format({ref_column_name: make_clickable,
                         test_column_name: make_clickable}).render()
    os.makedirs(dump_path, exist_ok=True)
    html_filepath = os.path.join(dump_path, '{}-vs-{}.html'.format(ref_name, test_name))
    csv_filepath = os.path.join(dump_path, '{}-vs-{}.csv'.format(ref_name, test_name))
    with open(html_filepath, 'w') as f:
        f.write(s)
    df.to_csv(csv_filepath)
