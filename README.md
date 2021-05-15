# Poll Vac

Implemented for Python 3.

Install the required Python modules via `pip`.

```bash
pip install -r requirements.txt
```

Then create a `settings.json` file with the structure of the [example](settings.json.example) file.
To get the actual URLs, you can use e.g. the Chrome dev tools and monitor the network tab.
When selecting a location and vaccination type, you can see the request URL in there.
However, the URLs in the example file seem to be quite stable, only the start date needs to be updated every day.

An audio file can be configured to be played when an available date is detected.
Download a file e.g. from [here](https://mixkit.co/free-sound-effects/alarm/) and configure the file name inside the settings file.

To start polling for dates, execute:

```
python poll.py
```
