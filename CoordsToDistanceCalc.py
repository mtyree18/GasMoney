from haversine import haversine, Unit
import csv_converter_01


#while list still being read
point1 = (38.03769, -78.46663)
point2 = (38.03769, -78.46664)

d = haversine(point1, point2, unit=Unit.MILES)

print(d)
