import praw
import tweepy
import json
import requests
import time
import os
import urllib.parse
from glob import glob



# twitter auth

CONSUMER_KEY = 'FQ3inobIDr0EuBkgUjhxps0zN'
CONSUMER_SECRET = '5I8zFNwS5MNjtV8dPfmC8kEcRybLLckI3oBKfPeHvEsWArObcE'
ACCESS_TOKEN = '1459323608992464900-BGv398n6nnO80cfgxWbGC0Fw62vCbS'
ACCESS_TOKEN_SECRET = 'WHgAighKDPoeoCNll7n030vEA3qVDxD0Kzasu8YsGLouc'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

#
# main bot code
#

# variables

hotLimit = 24

tweetSuffix = ''

imgDir = 'images' #image directory

postedCache = 'posted.txt' #cache for already posted

tweetMaxLength = 140

tweetDelay = 3600 #delay between tweets in seconds

subreddit = 'ooer'


def redditSetup(sub):
    print('setting up connection with reddit')
    reddit = praw.Reddit(
        user_agent='reddit Twitter tool monitoring ',
        client_id='alojLIlr1BwNAiqw3xpeiA',
        client_secret='i6YdLZKfw2JrbIXXtTGK_p51nbdH9w')
    return reddit.subreddit(sub)


def tweetCreator(subredditInfo):
    postDict = {}
    postIDs = []

    print('getting posts from reddit')

    top_ten = [x for x in subredditInfo.hot(limit=hotLimit) if not x.stickied][:20] # Check for sticky posts

    for submission in top_ten:
        if not alreadyTweeted(submission.id):
            # This stores a link to the reddit post itself
            # If you want to link to what the post is linking to instead, use
            # "submission.url" instead of "submission.permalink"
            postDict[submission.title] = {}
            post = postDict[submission.title]
            # post['link'] = submission.url

            # Store the url the post points to (if any)
            # If it's an imgur URL, it will later be downloaded and uploaded alongside the tweet
            post['imagePath'] = getImage(submission.url)

            postIDs.append(submission.id)
        else:
            print('already tweeted: {}'.format(str(submission)))

    return postDict, postIDs


def alreadyTweeted(postID):
    found = False
    with open(postedCache, 'r') as inFile:
        for line in inFile:
            if postID in line:
                found = True
                break
    return found


def stripTitle(title, numChar):
    #shortens to 140 char lmiit
    if len(title) <= numChar:
        return title
    else:
        return title[:numChar - 1] + '...'


def getImage(imageUrl):
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
    removeDir = os.listdir(path)
    for item in removeDir:
        if item.endswith(".gif"):
            os.remove(os.path.join(path), item)

def tweeter(postDict, postIDs):
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
    with open(postedCache, 'a') as outFile:
        outFile.write(str(postID) + '\n')

def main():


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