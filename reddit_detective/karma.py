"""
Let's assume that you get subreddits of 2 comments

Terminology: "stuff like karma" includes
comment_karma, link_karma, score, upvote_ratio and subscribers

If those 2 comments belong to the same subreddit, the code will be like the following:
    MERGE (:Subreddit ...)
    MERGE (:Subreddit ...)
If we include stuff like karma in properties at creation time,
then constraint UniqueSubreddit will fail.

Why?
Because Reddit does not give the exact number when it comes to
karmas/upvotes/subscribers. This leads to having different karma numbers
in 2 MERGE statements for the same Subreddit.

What is our solution?
    - Do not include stuff like karma in properties at creation time
    - After creation, get each node/rel's stuff like karma and add to their props
    What if the user adds more stuff to their database?
        - Delete each node/rel's stuff like karma
        - Then get each node/rel's stuff like karma and add to their props
    What if the user does not want to deal with stuff like karma?
        - Make it optional
"""
import praw
from neo4j import BoltDriver


def _set_subreddit_subscribers(api: praw.Reddit, name):
    sub = api.subreddit(name)
    return """
MATCH (n {id: "%s"})
WITH n
SET n.subscribers = %s;
""" % (sub.id, sub.subscribers)


def _set_submission_upvotes(api: praw.Reddit, id_):
    sub = api.submission(id_)
    return """
MATCH (n {id: "%s"})
WITH n
SET n.score = %s, n.upvote_ratio = %s;
""" % (sub.id, sub.score, sub.upvote_ratio)


def _set_redditor_karma(api: praw.Reddit, name):
    red = api.redditor(name)
    return """
MATCH (n {id: "%s"})
WITH n
SET n.comment_karma = %s, n.link_karma = %s
""" % (red.id, red.comment_karma, red.link_karma)


def _set_comment_score(api: praw.Reddit, id_):
    comm = api.comment(id_)
    return """
MATCH ()-[r:COMMENTED|REPLIED {id: "%s"}]-()
WITH r
SET r.score = %s;
""" % (comm.id, comm.score)


def _remove_stuff_subreddit():
    return """
MATCH (n:Subreddit)
WITH n
REMOVE n.subscribers;
"""


def _remove_stuff_submission():
    return """
MATCH (n:Submission)
WITH n
REMOVE n.score, n.upvote_ratio;
"""


def _remove_stuff_redditor():
    return """
MATCH (n:Redditor)
WITH n
REMOVE n.comment_karma, n.link_karma;
"""


def _remove_stuff_comment():
    return """
MATCH ()-[r:COMMENTED|REPLIED]-()
WITH r
REMOVE r.score;
"""


def _set_karma_subreddits(api, names):
    return [_set_subreddit_subscribers(api, name[0]) for name in list(names)]


def _set_karma_submissions(api, ids):
    return [_set_submission_upvotes(api, id_[0]) for id_ in list(ids)]


def _set_karma_redditors(api, names):
    return [_set_redditor_karma(api, name[0]) for name in list(names)]


def _set_karma_comments(api, ids):
    return [_set_comment_score(api, id_[0]) for id_ in list(ids)]


def _remove_karma():
    return [
        _remove_stuff_subreddit(),
        _remove_stuff_submission(),
        _remove_stuff_redditor(),
        _remove_stuff_comment()
    ]