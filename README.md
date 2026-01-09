# Call Your Loved Ones

I need to do a better job of staying in touch with the people who are important to me. Really, lots of us do.

So I built a little app that lets me add people to call, and tells me when I last called them. And that's it.

## Self-Hosting

The app is FastAPI with a Postgres database (although it really could be any SQL database, most likely - nothing fancy). You can run it with:

1. `docker compose up -d` to start the database.
2. `make install && make run` to run the app.
