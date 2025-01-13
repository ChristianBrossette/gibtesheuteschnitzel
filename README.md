# gibtesheuteschnitzel
I started this project and the webpage [gibtesheuteschnitzel.de](http://gibtesheuteschnitzel.de/) in 2015 during my master’s thesis at Saarland University. The original inspiration was the webpage [gibtesheutepommes.de](https://gibtesheutepommes.de/).

The primary purpose was to gain experience with web development, explore web hosting, and have some fun. I chose a simple approach to check whether Schnitzel is on the menu at the Mensa. A straightforward regular expression is used: `re.findall(r"Schnitzel|schnitzel", content)`. This means that other variations of Schnitzel, such as Cordon bleu, will be overlooked, but vegetarian or vegan Schnitzel are counted.

Not all changes to the webpage are on GitHub because I moved the project between platforms at some point.

## Code Quality
The quality of the code is not great. I relied heavily on string split operations to parse dates instead of using Python’s `datetime` package and its methods. The history of whether Schnitzel was detected on the Mensa menu is stored in a text file, `stats.txt`, which is a lazy solution. Ideally, a database should be used to store this history.

## Deployment
I use web hosting to deploy the Python script. It is executed at regular intervals using a cron daemon. During execution, the script generates and updates the HTML file for the webpage if changes are detected.