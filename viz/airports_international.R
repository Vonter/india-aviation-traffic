# Import required libraries
library(tidyverse)
library(scales)
library(hrbrthemes)
library(RColorBrewer)

# Read the CSV file
data <- "../aggregated/international/city.csv"
df <- read_csv(data)
df <- df %>%
  select(Year, Quarter, City1, City2, PaxToCity2, PaxFromCity2)

df <- df %>%
  group_by(Year, Quarter, City2) %>%
  summarise(Passengers = sum(PaxToCity2, na.rm = TRUE))
names(df)[names(df) == "City2"] <- "City"

# Keep only big cities
city_passenger_sums <- df %>%
  group_by(City) %>%
  summarise(total_passengers = sum(`Passengers`))
selected_cities <- city_passenger_sums %>%
  filter(total_passengers >= 6000000) %>%
  pull(City)
df <- df %>%
  filter(City %in% selected_cities)

# Group by year and Quarter
df <- df %>%
  mutate(Date = as.Date(paste(
    paste("20", Year, sep = ""), sprintf("%s", Quarter * 3), "01", sep = "-"
  ))) %>%
  select(City, Date, `Passengers`) %>%
  distinct()

# Order cities by their final passenger numbers
cities <- df %>%
  group_by(City) %>%
  filter(Date == max(Date)) %>%
  arrange(desc(`Passengers`)) %>%
  pull(City)

# Set factor levels in reverse order to show top cities at the top of the legend
df$City <- factor(df$City, levels = rev(cities))

# Create the plot
p <- ggplot(df, aes(
  x = Date,
  y = `Passengers`,
  group = City,
  color = City
)) +
  geom_line(
    data = df %>% filter(!City %in% cities),
    alpha = 0.4,
    size = 0.5
  ) +
  geom_line(data = df %>% filter(City %in% cities), size = 1.2) +
  ggtitle("International air ridership in India (by city)") +
  
  # Modify x-axis scale
  scale_x_date(
    date_breaks = "1 year",
    date_labels = "%Y",
    expand = c(0.02, 0)
  ) +
  
  # Modify y-axis scale
  scale_y_continuous(
    labels = scales::comma_format(scale = 1e-6, suffix = "M"),
    breaks = scales::pretty_breaks(n = 6),
    expand = c(0.02, 0)
  ) +
  
  # Apply a modified theme based on theme_ipsum() with white background and improved axis labels
  theme_ipsum() +
  theme(
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA),
    plot.title = element_text(hjust = 0.5, size = 16, face = "bold"),
    axis.title = element_text(size = 20, face = "bold"),
    # Larger and bold axis titles
    axis.title.x = element_text(
      margin = margin(t = 20),
      hjust = 0.5,
      size = 16,
      face = "bold"
    ),
    # Centered x-axis title
    axis.title.y = element_text(
      margin = margin(r = 20),
      hjust = 0.5,
      size = 16,
      angle = 90,
      face = "bold"
    ),
    # Centered y-axis title
    axis.text = element_text(size = 12),
    # Larger axis text
    legend.position = "right",
    legend.background = element_rect(fill = "white", color = NA),
    legend.title = element_blank(),
    panel.grid.minor = element_blank(),
    legend.key.size = unit(1, "cm"),
    # Increase legend key size
    legend.text = element_text(size = 10)  # Adjust legend text size
  ) +
  
  # Add labels
  labs(x = "Year", y = "Quarterly Passengers (International)", color = "City") +
  
  guides(colour = guide_legend(reverse = T))

# Print the plot
print(p)

# Save the plot with a white background
ggsave(
  "airports_international.png",
  plot = p,
  width = 12,
  height = 8,
  dpi = 300,
  bg = "white"
)
