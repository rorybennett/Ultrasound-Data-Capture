from pathlib import Path


def createInitialDirectories() -> (Path, Path):
    """
    Create the initial directories needed for file storage, if they do not already exist. The two directories needed
    are the Generated/SingleFrames directory and the Generated/Videos directory, for storing snapshots and
    subdirectories containing video recordings, respectively. The Generated/Videos subdirectories are generated as
    they are needed.

    Returns:
        singleFramesPath (Path): Path of the SingleFrames directory.
        videosPath (Path): Path of the Videos directory.
    """
    currentWorkingDirectory = Path.cwd()

    singleFramesPath = Path(currentWorkingDirectory, 'Generated/SingleFrames')
    singleFramesPath.mkdir(parents=True, exist_ok=True)

    videosPath = Path(currentWorkingDirectory, 'Generated/Videos')
    videosPath.mkdir(parents=True, exist_ok=True)

    return singleFramesPath, videosPath
