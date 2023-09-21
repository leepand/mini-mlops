import argparse
import sys
import os
from datetime import datetime


from .config import gitconfig_user_get, gitconfig_read
from .create import repo_create, repo_find
from .create import (
    object_read,
    object_find,
    tree_checkout,
    tree_from_index,
    commit_create,
    tag_create,
)
from .add import add
from .index import index_read
from .branch import branch_get_active
from .file import repo_file
from .hash import cmd_hash_object
from .log import cmd_log
from .rm import rm
from .ref import ref_list, show_ref


argparser = argparse.ArgumentParser(description="The stupid content tracker")

argsubparsers = argparser.add_subparsers(title="Command", dest="command")
argsubparsers.required = True

argsp = argsubparsers.add_parser("init", help="Initialize a new empty repository.")
argsp.add_argument(
    "path",
    metavar="directory",
    nargs="?",
    default=".",
    help="Where to create the repository.",
)

argsp = argsubparsers.add_parser(
    "cat-file", help="Provide content of repository objects"
)

argsp.add_argument(
    "type",
    metavar="type",
    choices=["blob", "commit", "tag", "tree"],
    help="Specify the type",
)

argsp.add_argument("object", metavar="object", help="The object to display")

argsp = argsubparsers.add_parser(
    "hash-object", help="Compute object ID and optionally creates a blob from a file"
)

argsp.add_argument(
    "-t",
    metavar="type",
    dest="type",
    choices=["blob", "commit", "tag", "tree"],
    default="blob",
    help="Specify the type",
)

argsp.add_argument(
    "-w",
    dest="write",
    action="store_true",
    help="Actually write the object into the database",
)

argsp.add_argument("path", help="Read object from <file>")


argsp = argsubparsers.add_parser("log", help="Display history of a given commit.")
argsp.add_argument("commit", default="HEAD", nargs="?", help="Commit to start at.")

argsp = argsubparsers.add_parser("ls-tree", help="Pretty-print a tree object.")
argsp.add_argument("object", help="The object to show.")


argsp = argsubparsers.add_parser(
    "checkout", help="Checkout a commit inside of a directory."
)

argsp.add_argument("commit", help="The commit or tree to checkout.")

argsp.add_argument("path", help="The EMPTY directory to checkout on.")


argsp = argsubparsers.add_parser("show-ref", help="List references.")


argsp = argsubparsers.add_parser("tag", help="List and create tags")

argsp.add_argument(
    "-a",
    action="store_true",
    dest="create_tag_object",
    help="Whether to create a tag object",
)

argsp.add_argument("name", nargs="?", help="The new tag's name")

argsp.add_argument(
    "object", default="HEAD", nargs="?", help="The object the new tag will point to"
)

argsp = argsubparsers.add_parser(
    "rev-parse", help="Parse revision (or other objects )identifiers"
)

argsp.add_argument(
    "--wyag-type",
    metavar="type",
    dest="type",
    choices=["blob", "commit", "tag", "tree"],
    default=None,
    help="Specify the expected type",
)

argsp.add_argument("name", help="The name to parse")


# ███████ ██    ██ ███    ██  ██████ ████████ ██  ██████  ███    ██ ███████
# ██      ██    ██ ████   ██ ██         ██    ██ ██    ██ ████   ██ ██
# █████   ██    ██ ██ ██  ██ ██         ██    ██ ██    ██ ██ ██  ██ ███████
# ██      ██    ██ ██  ██ ██ ██         ██    ██ ██    ██ ██  ██ ██      ██
# ██       ██████  ██   ████  ██████    ██    ██  ██████  ██   ████ ███████


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    if args.command == "add":
        cmd_add(args)
    elif args.command == "cat-file":
        cmd_cat_file(args)
    elif args.command == "checkout":
        cmd_checkout(args)
    elif args.command == "commit":
        cmd_commit(args)
    elif args.command == "hash-object":
        cmd_hash_object(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "log":
        cmd_log(args)
    elif args.command == "ls-tree":
        cmd_ls_tree(args)

    elif args.command == "rev-parse":
        cmd_rev_parse(args)
    elif args.command == "rm":
        cmd_rm(args)
    elif args.command == "show-ref":
        cmd_show_ref(args)
    elif args.command == "tag":
        cmd_tag(args)


def cmd_init(args):
    repo_create(args.path)


def cmd_add(args):
    repo = repo_find()
    add(repo, args.path)


def cmd_checkout(args):
    repo = repo_find()

    obj = object_read(repo, object_find(repo, args.commit))

    # If the object is a commit, we grab its tree
    if obj.fmt == b"commit":
        obj = object_read(repo, obj.kvlm[b"tree"].decode("ascii"))

    # Verify that path is an empty directory
    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception("Not a directory {0}!".format(args.path))
        if os.listdir(args.path):
            raise Exception("Not empty {0}!".format(args.path))
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))


def cmd_cat_file(args):
    repo = repo_find()
    cat_file(repo, args.object, fmt=args.type.encode())


def cat_file(repo, obj, fmt=None):
    obj = object_read(repo, object_find(repo, obj, fmt=fmt))
    sys.stdout.buffer.write(obj.serialize())


def cmd_commit(args):
    repo = repo_find()
    index = index_read(repo)
    # Create trees, grab back SHA for the root tree.
    tree = tree_from_index(repo, index)

    # Create the commit object itself
    commit = commit_create(
        repo,
        tree,
        object_find(repo, "HEAD"),
        gitconfig_user_get(gitconfig_read()),
        datetime.now(),
        args.message,
    )

    # Update HEAD so our commit is now the tip of the active branch.
    active_branch = branch_get_active(repo)
    if active_branch:  # If we're on a branch, we update refs/heads/BRANCH
        with open(
            repo_file(repo, os.path.join("refs/heads", active_branch)), "w"
        ) as fd:
            fd.write(commit + "\n")
    else:  # Otherwise, we update HEAD itself.
        with open(repo_file(repo, "HEAD"), "w") as fd:
            fd.write("\n")


def cmd_ls_tree(args):
    repo = repo_find()
    ls_tree(repo, args.tree, args.recursive)


def ls_tree(repo, ref, recursive=None, prefix=""):
    sha = object_find(repo, ref, fmt=b"tree")
    obj = object_read(repo, sha)
    for item in obj.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        if type == b"04":
            type = "tree"
        elif type == b"10":
            type = "blob"  # A regular file.
        elif type == b"12":
            type = "blob"  # A symlink. Blob contents is link target.
        elif type == b"16":
            type = "commit"  # A submodule
        else:
            raise Exception("Weird tree leaf mode {}".format(item.mode))

        if not (recursive and type == "tree"):  # This is a leaf
            print(
                "{0} {1} {2}\t{3}".format(
                    "0" * (6 - len(item.mode)) + item.mode.decode("ascii"),
                    # Git's ls-tree displays the type
                    # of the object pointed to.  We can do that too :)
                    type,
                    item.sha,
                    os.path.join(prefix, item.path),
                )
            )
        else:  # This is a branch, recurse
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))


def cmd_rm(args):
    repo = repo_find()
    rm(repo, args.path)


def cmd_tag(args):
    repo = repo_find()

    if args.name:
        tag_create(
            repo,
            args.name,
            args.object,
            type="object" if args.create_tag_object else "ref",
        )
    else:
        refs = ref_list(repo)
        show_ref(repo, refs["tags"], with_hash=False)


def cmd_show_ref(args):
    repo = repo_find()
    refs = ref_list(repo)
    show_ref(repo, refs, prefix="refs")


def cmd_rev_parse(args):
    if args.type:
        fmt = args.type.encode()
    else:
        fmt = None

    repo = repo_find()

    print(object_find(repo, args.name, fmt, follow=True))
