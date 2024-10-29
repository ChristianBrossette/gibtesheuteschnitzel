# gibtesheuteschnitzel

I have started this project and the webpage [gibtesheuteschnitzel.de](http://gibtesheuteschnitzel.de/) in 2015 during my master thesis at Saarland University. The original inspiration was the webpage [gibtesheutepommes.de](https://gibtesheutepommes.de/).

The sole purpose was to get some experience with webspaces, webpages and to have some fun. I choose a simple approach to check whether a Schnitzel is on the menue of the Mensaar. A simple regular expression is used  `re.findall(r"Schnitzel|schnitzel", content)`. This meas that other kinds of Schnitzel such as Cordon bleu will be overlooked but vegetarian or vegan Schnitzel are counted.

Not all changes to the webpage are on github since I moved the project inbetween on this platform.

## Code quality

The quality of the code is not good. I have used a lot of string split operations to parse dates instead of using the Python package `datetime` and its methods. The history of whether a Schnitzel was detected on the menue of Mensaar is stored in a text file `stats.txt`, which is lazy. A database for the history would be the prevered way.

## Deployment

I am using a webspace to host the python skript. It is executed in a regular interval with a cron-deamon. While executing the script the html file for the webpage is created and update, if changes were detected.