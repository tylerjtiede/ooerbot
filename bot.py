import praw
import tweepy
import json
import requests
import time
import os
import urllib.parse
from glob import glob
from dotenv import load_dotenv, dotenv_values

load_dotenv()

# keys

# twitter
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

# reddit
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# variables

hotLimit = 50

tweetSuffix = ''

imgDir = 'images' #image directory

postedCache = 'posted.txt' #cache for already posted

tweetMaxLength = 140

tweetDelay = 3600 #delay between tweets in seconds

subreddit = 'ooer'

#
# main bot code
#

def redditSetup(sub):
    print('setting up connection with reddit')
    reddit = praw.Reddit(
        user_agent='reddit Twitter tool monitoring ',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET)
    return reddit.subreddit(sub)


def tweetCreator(subredditInfo):
    # pulls posts from reddit, excluding stickied posts
    postDict = {}
    postIDs = []

    print('getting posts from reddit')

    top_ten = [x for x in subredditInfo.hot(limit=hotLimit) if not x.stickied][:40] # Check for sticky posts

    for submission in top_ten:
        if not alreadyTweeted(submission.id):
            # This stores a link to the reddit post itself
            # If you want to link to what the post is linking to instead, use
            # "submission.url" instead of "submission.permalink"
            postDict[submission.title] = {}
            post = postDict[submission.title]

            # Store the url the post points to (if any)
            # If it's an imgur URL, it will later be downloaded and uploaded alongside the tweet
            post['imagePath'] = getImage(submission.url)

            postIDs.append(submission.id)
        else:
            print('already tweeted: {}'.format(str(submission)))

    return postDict, postIDs


def alreadyTweeted(postID):
    # checks posted.txt for the post id to avoid duplicates
    found = False
    with open(postedCache, 'r') as inFile:
        for line in inFile:
            if postID in line:
                found = True
                break
    return found


def stripTitle(title, numChar):
    # shortens to 140 char lmiit
    if len(title) <= numChar:
        return title
    else:
        return title[:numChar - 1] + '...'


def getImage(imageUrl):
    # gets the images then downloads them if they are the right url type
    # won't download i.redd.it posts with .gif extension
    # since gifs tend to cause issues when posting to twitter
    if 'imgur.com' in imageUrl or 'i.redd.it' in imageUrl:
        fileName = os.path.basename(urllib.parse.urlsplit(imageUrl).path)
        if not '.gif' in fileName:
            imagePath = imgDir + '/' + fileName
            print('downloading image at url ' + imageUrl + '  to  ' + imagePath)
            resp = requests.get(imageUrl, stream=True)
            if resp.status_code == 200:
                with open(imagePath, 'wb') as imageFile:
                    for chunk in resp:
                        imageFile.write(chunk)
                return imagePath
            else:
                print('image failed to download. status code:' + resp.status_code)
    else:
        print('post doesn\'t point to an i.imgur.com or i.redd.it link')
    return ''

def removeGif(path):
    # function to remove gifs from img directory if necessary. not currently being used
    removeDir = os.listdir(path)
    for item in removeDir:
        if item.endswith(".gif"):
            os.remove(os.path.join(path), item)

def tweeter(postDict, postIDs):
    # creates the tweet
    for post, postID in zip(postDict, postIDs):
        imagePath = postDict[post]['imagePath']

        postText = stripTitle(post, tweetMaxLength)
        print('posting this on twitter')
        print(postText)
        if imagePath:
            print('with image ' + imagePath)
            api.update_status_with_media(filename=imagePath, status=postText)
        else:
            api.update_status(status=postText)
        logTweet(postID)
        time.sleep(tweetDelay)


def logTweet(postID):
    # logs post id in posted.txt cache
    with open(postedCache, 'a') as outFile:
        outFile.write(str(postID) + '\n')

def main():
    #runs through everything
    if not os.path.exists(postedCache):
        with open(postedCache, 'w'):
            pass
    if not os.path.exists(imgDir):
        os.makedirs(imgDir)

    sub = redditSetup(subreddit)
    postDict, postIDs = tweetCreator(sub)
    tweeter(postDict, postIDs)


    for filename in glob(imgDir + '/*'):
        os.remove(filename)


if __name__ == '__main__':
    main()