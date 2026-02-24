import praw
import os
import sqlite3
import time
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()


class ResourceBot:
    def __init__(self):
        # Authenticate with Reddit
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD")
        )
        self.db_name = "bot_memory.db"
        self._setup_db()

    def _setup_db(self):
        """Creates a database to track replied-to comments to avoid spamming."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS processed (id TEXT PRIMARY KEY)")
            conn.commit()

    def has_replied(self, comment_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute("SELECT id FROM processed WHERE id=?", (comment_id,))
            return cursor.fetchone() is not None

    def mark_replied(self, comment_id):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("INSERT INTO processed (id) VALUES (?)", (comment_id,))
            conn.commit()

    def run(self, subreddit_names):
        print(f"Bot started. Monitoring: {subreddit_names}")
        subreddit = self.reddit.subreddit(subreddit_names)

        # Stream comments in real-time
        for comment in subreddit.stream.comments(skip_existing=True):
            try:
                # Logic: Trigger word + check if we already replied
                if "!getlink" in comment.body.lower() and not self.has_replied(comment.id):

                    # Prevent the bot from replying to itself
                    if comment.author == self.reddit.user.me():
                        continue

                    print(f"Responding to {comment.author} in r/{comment.subreddit}")

                    reply_text = (
                        f"Beep boop! u/{comment.author}, here is the resource you requested:\n\n"
                        "[Community Resource Link](https://example.com)\n\n"
                        "***\n*I am a bot. Use !ignore to stop these replies.*"
                    )

                    comment.reply(body=reply_text)
                    self.mark_replied(comment.id)

                    # Respect API limits by pausing slightly
                    time.sleep(1)

            except Exception as e:
                print(f"Error encountered: {e}")
                time.sleep(10)  # Wait before retrying


if __name__ == "__main__":
    bot = ResourceBot()
    # Replace with the subreddits you want to monitor
    bot.run("test+learnprogramming")