# last.fm scripts

The aim of these scripts is to get all your loved songs from last.fm, saved them to a spreadsheet, which we can then use in another script to search your PC for the song matches so we can generate an .m3u playlist file of all our loved tracks locally.



`get_last_fm_loved_tracks.py` - This will get all your loved songs from last.fm and save to a .csv file.

make sure yaml is installed.

`pip install pyyaml`

and update the config file with your last.fm credentials.


```
api:
  key: "xxxx"
  user: "xxxxxx"

output:
  file: "loved_tracks.csv"
```