"""

"""


def main():
    import matplotlib.pyplot as plt
    from PIL import Image
    import numpy as np
    from dtlpy import PlatformInterface
    from dtlpy.utilities.annotations import ImageAnnotation

    # init platform interface
    dlp = PlatformInterface()

    # get project and dataset
    dataset = dlp.projects.get('MyProject').datasets.get('MyDataset')

    # image filepath
    image_filepath = r'E:\Images\img_000.png'
    # annotations filepath - RGB with color for each label
    annotations_filepath = r'E:\annotations\img_000.png'

    # upload item to root directory
    item = dataset.items.upload(image_filepath, remote_path='/')

    # read mask from file
    mask = np.array(Image.open(annotations_filepath))

    # get unique color (labels)
    unique_colors = np.unique(mask.reshape(-1, mask.shape[2]), axis=0)

    # init dataloop annotations builder
    ann = ImageAnnotation()
    # for each label - create a dataloop mask annotation
    for i, color in enumerate(unique_colors):
        print(color)
        if i == 0:
            # ignore background
            continue
        # get mask of same color
        class_mask = np.all(color == mask, axis=2)
        # # plot mask for debug
        # plt.figure()
        # plt.imshow(class_mask)
        # add annotation to builder
        ann.add_annotation(pts=class_mask, label=str(i), annotation_type='binary', color=color)
    # upload all annotations
    item.annotations.upload(ann.to_platform())
