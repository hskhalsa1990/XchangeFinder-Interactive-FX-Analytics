# R data analysis starter
# Download CSV: http://127.0.0.1:8000/analytics/export.csv
rates <- read.csv("xchangefinder_rates.csv")
print(summary(rates$rate))
