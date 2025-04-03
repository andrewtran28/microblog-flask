import os

# This sets the environment variable to use an in-memory SQLite database during tests so the existing one is unaltered
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import User, Post


class UserModelCase(unittest.TestCase):
    # Create an application context and pushed it
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

        # creates all the database tables; useful for quickly creating a database for testing
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username="susan", email="susan@@example.com")
        u.set_password("cat")
        self.assertFalse(u.check_password("dog"))
        self.assertTrue(u.check_password("cat"))

    def test_avatar(self):
        u = User(username="john", email="john@example.com")
        self.assertEqual(
            u.avatar(128),
            "https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128",
        )

    def test_follow(self):
        u1 = User(username="john", email="john@example.com")
        u2 = User(username="susan", email="susan@example.com")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        following = db.session.scalars(u1.following.select()).all()
        followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 1)
        self.assertEqual(u2.followers_count(), 1)
        u1_following = db.session.scalars(u1.following.select()).all()
        u2_followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(u1_following[0].username, "susan")
        self.assertEqual(u2_followers[0].username, "john")

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

    def test_follow_posts(self):
        # Mock four users and four posts
        u1 = User(username="john", email="john@example.com")
        u2 = User(username="susan", email="susan@example.com")
        u3 = User(username="mary", email="mary@example.com")
        u4 = User(username="david", email="david@example.com")
        db.session.add_all([u1, u2, u3, u4])

        now = datetime.now(timezone.utc)
        p1 = Post(
            body="This is a a post from John",
            author=u1,
            timestamp=now + timedelta(seconds=1),
        )
        p2 = Post(
            body="This is a a post from Susan",
            author=u2,
            timestamp=now + timedelta(seconds=4),
        )
        p3 = Post(
            body="This is a a post from Mary",
            author=u3,
            timestamp=now + timedelta(seconds=3),
        )
        p4 = Post(
            body="This is a a post from David",
            author=u4,
            timestamp=now + timedelta(seconds=2),
        )
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed users posts
        f1 = db.session.scalars(u1.following_posts()).all()
        f2 = db.session.scalars(u2.following_posts()).all()
        f3 = db.session.scalars(u3.following_posts()).all()
        f4 = db.session.scalars(u4.following_posts()).all()
        self.assertEqual(
            f1, [p2, p4, p1]
        )  # john should see susan, david and his own post
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

    # Make a test for pagination
    def test_pagination(self):
        u1 = User(username="john", email="john@example.com")
        db.session.add(u1)
        db.session.commit()
        for i in range(30):
            db.session.add(Post(body=f"post from john {i}", author=u1))
        db.session.commit()
        # response = self.client.get(url_for("user", username="john"))
        # self.assertEqual(response.status_code, 200)
        # self.assertTrue("pagination" in response.get_json().keys())


if __name__ == "__main__":
    unittest.main(verbosity=2)
