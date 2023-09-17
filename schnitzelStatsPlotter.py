from dateutil import parser
import matplotlib.pyplot as plt


schnitzelPerWeek = {0:0, 1:0, 2:0, 3:0, 4:0}
with open("stats.txt", "r") as f:
    for line in f:
        weekday = parser.parse(line.strip().split("_")[0]).weekday()
        schnitzelStatus = str(line.strip().split("_")[1])
        if schnitzelStatus == "ja":
            schnitzelPerWeek[weekday] += 1

print(schnitzelPerWeek)
offset = 50
df = pd.DataFrame({'Wochentage': [x - offset for x in schnitzelPerWeek.values()]}, index=["Mo", "Di", "Mi", "Do", "Fr",])
plt.bar([0, 1, 2, 3, 4], [x - offset for x in schnitzelPerWeek.values()], bottom=offset, align='center')
plt.title('Schnitzel pro Wochentag')
plt.ylabel('Tage')
plt.xlabel('Wochentag')
plt.xticks([0, 1, 2, 3, 4], ["Mo", "Di", "Mi", "Do", "Fr",])
plt.savefig("schnitzelStatsWeekday.png", dpi=300)
