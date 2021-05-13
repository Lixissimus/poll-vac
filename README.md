# Poll Vac

Install the required Python modules via `pip`.
Then create a `settings.json` file with the structure of the [example](settings.json.example) file.
To get the actual URLs, you can use e.g. the Chrome dev tools and monitor the network tab.
When selecting a location and vaccination type, you can see the request URL in there.

To start polling, execute:

```
python poll.py
```
