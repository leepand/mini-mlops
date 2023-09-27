import argparse
import sys
import os
from datetime import datetime
import grp, pwd
from fnmatch import fnmatch


from .config import gitconfig_user_get, gitconfig_read
from .create import repo_create, repo_find
from .create import (
    object_read,
    object_find,
    tree_checkout,
    tree_from_index,
    commit_create,
    tag_create,
    object_hash,
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


def cmd_checkout(commit, path):
    repo = repo_find()

    obj = object_read(repo, object_find(repo, commit))

    # If the object is a commit, we grab its tree
    if obj.fmt == b"commit":
        obj = object_read(repo, obj.kvlm[b"tree"].decode("ascii"))

    # Verify that path is an empty directory
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise Exception("Not a directory {0}!".format(path))
        if os.listdir(path):
            raise Exception("Not empty {0}!".format(path))
    else:
        os.makedirs(path)

    tree_checkout(repo, obj, os.path.realpath(path))


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
            if isinstance(item.path, bytes):
                item.path = item.path.decode()
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
            if isinstance(item.path, bytes):
                item.path = item.path.decode()
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
            # ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))


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


def gitignore_parse1(raw):
    raw = raw.strip()  # Remove leading/trailing spaces

    if not raw or raw[0] == "#":
        return None
    elif raw[0] == "!":
        return (raw[1:], False)
    elif raw[0] == "\\":
        return (raw[1:], True)
    else:
        return (raw, True)


def gitignore_parse(lines):
    ret = list()

    for line in lines:
        parsed = gitignore_parse1(line)
        if parsed:
            ret.append(parsed)

    return ret


class GitIgnore(object):
    absolute = None
    scoped = None

    def __init__(self, absolute, scoped):
        self.absolute = absolute
        self.scoped = scoped


def gitignore_read(repo):
    ret = GitIgnore(absolute=list(), scoped=dict())

    # Read local configuration in .git/info/exclude
    repo_file = os.path.join(repo.gitdir, "info/exclude")
    if os.path.exists(repo_file):
        with open(repo_file, "r") as f:
            ret.absolute.append(gitignore_parse(f.readlines()))

    # Global configuration
    if "XDG_CONFIG_HOME" in os.environ:
        config_home = os.environ["XDG_CONFIG_HOME"]
    else:
        config_home = os.path.expanduser("~/.config")
    global_file = os.path.join(config_home, "git/ignore")

    if os.path.exists(global_file):
        with open(global_file, "r") as f:
            ret.absolute.append(gitignore_parse(f.readlines()))

    # .gitignore files in the index
    index = index_read(repo)

    for entry in index.entries:
        if entry.name == ".gitignore" or entry.name.endswith("/.gitignore"):
            dir_name = os.path.dirname(entry.name)
            contents = object_read(repo, entry.sha)
            lines = contents.blobdata.decode("utf8").splitlines()
            ret.scoped[dir_name] = gitignore_parse(lines)
    return ret


def check_ignore1(rules, path):
    result = None
    for (pattern, value) in rules:
        if fnmatch(path, pattern):
            result = value
    return result


def check_ignore_absolute(rules, path):
    parent = os.path.dirname(path)
    for ruleset in rules:
        result = check_ignore1(ruleset, path)
        if result != None:
            return result
    return False  # This is a reasonable default at this point.


def check_ignore_scoped(rules, path):
    parent = os.path.dirname(path)
    while True:
        if parent in rules:
            result = check_ignore1(rules[parent], path)
            if result != None:
                return result
        if parent == "":
            break
        parent = os.path.dirname(parent)
    return None


def check_ignore(rules, path):
    if os.path.isabs(path):
        raise Exception(
            "This function requires path to be relative to the repository's root"
        )

    result = check_ignore_scoped(rules.scoped, path)
    if result != None:
        return result

    return check_ignore_absolute(rules.absolute, path)


def cmd_check_ignore(args):
    repo = repo_find()
    rules = gitignore_read(repo)
    for path in args.path:
        if check_ignore(rules, path):
            print(path)


def cmd_ls_files(verbose=True):
    repo = repo_find()
    index = index_read(repo)
    commit_files = []
    if verbose:
        print(
            "Index file format v{}, containing {} entries.".format(
                index.version, len(index.entries)
            )
        )

    for e in index.entries:
        print(e.name)
        commit_files.append(e.name)
        if verbose:
            print(
                "  {} with perms: {:o}".format(
                    {0b1000: "regular file", 0b1010: "symlink", 0b1110: "git link"}[
                        e.mode_type
                    ],
                    e.mode_perms,
                )
            )
            print("  on blob: {}".format(e.sha))
            print(
                "  created: {}.{}, modified: {}.{}".format(
                    datetime.fromtimestamp(e.ctime[0]),
                    e.ctime[1],
                    datetime.fromtimestamp(e.mtime[0]),
                    e.mtime[1],
                )
            )
            print("  device: {}, inode: {}".format(e.dev, e.ino))
            print(
                "  user: {} ({})  group: {} ({})".format(
                    pwd.getpwuid(e.uid).pw_name,
                    e.uid,
                    grp.getgrgid(e.gid).gr_name,
                    e.gid,
                )
            )
            print(
                "  flags: stage={} assume_valid={}".format(
                    e.flag_stage, e.flag_assume_valid
                )
            )

    return commit_files


def cmd_tag(name_tag="mlops-tag", object_tag="HEAD", create_tag_object="tag"):
    repo = repo_find()

    if name_tag:
        tag_create(
            repo,
            name_tag,
            object_tag,
            create_tag_object=True if create_tag_object == "tag" else False,
        )
    else:
        refs = ref_list(repo)
        show_ref(repo, refs["tags"], with_hash=False)


def cmd_status_branch(repo):
    branch = branch_get_active(repo)
    if branch:
        print("On branch {}.".format(branch))
    else:
        print("HEAD detached at {}".format(object_find(repo, "HEAD")))


def tree_to_dict(repo, ref, prefix=""):
    ret = dict()
    tree_sha = object_find(repo, ref, fmt=b"tree")

    tree = object_read(repo, tree_sha)

    for leaf in tree.items:
        if isinstance(leaf.path, bytes):
            leaf.path = leaf.path.decode()
        # print(type(prefix), "fff", type(leaf.path))
        full_path = os.path.join(prefix, leaf.path)

        # We read the object to extract its type (this is uselessly
        # expensive: we could just open it as a file and read the
        # first few bytes)
        is_subtree = leaf.mode.startswith(b"04")
        # is_subtree = False
        # Depending on the type, we either store the path (if it's a
        # blob, so a regular file), or recurse (if it's another tree,
        # so a subdir)
        if is_subtree:
            # ret.update(tree_to_dict(repo, leaf.sha, full_path))
            try:
                ret.update(tree_to_dict(repo, leaf.sha, full_path))
            except:
                continue

        else:
            ret[full_path] = leaf.sha

    return ret


def cmd_status_head_index(repo, index):
    print("Changes to be committed:")

    head = tree_to_dict(repo, "HEAD")
    seen_sha = set()  # 用于存储已经出现过的 entry.sha 值
    for entry in index.entries:
        if entry.sha in seen_sha:
            continue  # 跳过已经出现过的 entry.sha
        else:
            seen_sha.add(entry.sha)  # 将新的 entry.sha 添加到集合中
            if entry.name in head:
                if head[entry.name] != entry.sha:
                    print("  modified:", entry.name)
                del head[entry.name]  # Delete the key
            else:
                print("  added:   ", entry.name)

    # Keys still in HEAD are files that we haven't met in the index,
    # and thus have been deleted.
    for entry in head.keys():
        print("  deleted: ", entry)


def cmd_status_index_worktree(repo, index):
    print("Changes not staged for commit:")

    ignore = gitignore_read(repo)

    gitdir_prefix = repo.gitdir + os.path.sep

    all_files = list()

    # We begin by walking the filesystem
    for (root, _, files) in os.walk(repo.worktree, True):
        if root == repo.gitdir or root.startswith(gitdir_prefix):
            continue
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo.worktree)
            all_files.append(rel_path)

    # We now traverse the index, and compare real files with the cached
    # versions.

    seen_sha = set()  # 用于存储已经出现过的 entry.sha 值

    for entry in index.entries:
        if entry.sha in seen_sha:
            continue  # 跳过已经出现过的 entry.sha
        else:
            seen_sha.add(entry.sha)  # 将新的 entry.sha 添加到集合中
        full_path = os.path.join(repo.worktree, entry.name)

        # That file *name* is in the index

        if not os.path.exists(full_path):
            print("  deleted: ", entry.name)
        else:
            stat = os.stat(full_path)

            # Compare metadata
            ctime_ns = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns = entry.mtime[0] * 10**9 + entry.mtime[1]
            if (stat.st_ctime_ns != ctime_ns) or (stat.st_mtime_ns != mtime_ns):
                # If different, deep compare.
                # @FIXME This *will* crash on symlinks to dir.
                with open(full_path, "rb") as fd:
                    new_sha = object_hash(fd, b"blob", None)
                    # If the hashes are the same, the files are actually the same.
                    same = entry.sha == new_sha

                    if not same:
                        print("  modified:", entry.name)

        if entry.name in all_files:
            all_files.remove(entry.name)

    print()
    print("Untracked files:")

    for f in all_files:
        # @TODO If a full directory is untracked, we should display
        # its name without its contents.
        if not check_ignore(ignore, f):
            print(" ", f)


def cmd_status(_):
    repo = repo_find()
    index = index_read(repo)

    cmd_status_branch(repo)
    cmd_status_head_index(repo, index)
    print()
    cmd_status_index_worktree(repo, index)
