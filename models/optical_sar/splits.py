from torch.utils.data import Subset


def create_scene_split(dataset):

    train_indices = []
    validation_indices = []
    test_indices = []

    for index, (scene_index, patch_index) in enumerate(
        dataset.index_map
    ):

        scene_name = dataset.scene_names[scene_index]

        if scene_name in ["scene_001", "scene_002", "scene_003"]:

            train_indices.append(index)

        elif scene_name == "scene_004":

            validation_indices.append(index)

        elif scene_name == "scene_005":

            test_indices.append(index)

    train_dataset = Subset(
        dataset,
        train_indices
    )

    validation_dataset = Subset(
        dataset,
        validation_indices
    )

    test_dataset = Subset(
        dataset,
        test_indices
    )

    return (
        train_dataset,
        validation_dataset,
        test_dataset
    )   