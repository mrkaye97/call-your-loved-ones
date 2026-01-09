# Call Your Loved Ones

I need to do a better job of staying in touch with the people who are important to me. Really, lots of us do.

So I built a little app that lets me add people to call, and tells me when I last called them. And that's it.

## Using the "managed" version

The app is running on [my website](https://cylo.mkaye.dev), and is hosted on my RaspberryPi at home. If you use it anonymously, it'll just store your data in local storage in your browser, so none of your personal data will travel to my server. If you want to make an account, I'll store a (hashed) password, your username, and whichever names you add in a database also running on my Pi.

## Self-Hosting

The app is FastAPI (but mostly just HTML) with a Postgres database (although it really could be any SQL database, most likely - nothing fancy). You can run it with:

1. `docker compose up -d` to start the database.
2. `make install && make run` to run the app.
