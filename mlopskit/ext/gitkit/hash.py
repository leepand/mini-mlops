from .create import object_write, GitTree, GitTag, GitBlob, repo_find, GitCommit


def object_hash(fd, fmt, repo=None):
    """Hash object, writing it to repo if provided."""
    data = fd.read()

    # Choose constructor according to fmt argument
    if fmt == b"commit":
        obj = GitCommit(data)
    elif fmt == b"tree":
        obj = GitTree(data)
    elif fmt == b"tag":
        obj = GitTag(data)
    elif fmt == b"blob":
        obj = GitBlob(repo, data)
    else:
        raise Exception("Unknown type %s!" % fmt.decode("ascii"))

    return object_write(obj, repo)


def cmd_hash_object(args):
    if args.write:
        repo = repo_find()
    else:
        repo = None

    with open(args.path, "rb") as fd:
        sha = object_hash(fd, args.type.encode(), repo)
        print(sha)
