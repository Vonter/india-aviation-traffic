# Import required libraries
library(tidyverse)
library(scales)
library(hrbrthemes)
library(RColorBrewer)
library(stringr)

# Read the CSV file
data <- "../aggregated/international/carrier_quarterly.csv"
df <- read_csv(data)
df <- df %>%
  select(Year, Quarter, Airline, PaxToIndia, PaxFromIndia)
df$Passengers <- df$PaxToIndia + df$PaxFromIndia
df <- df %>% select(-PaxToIndia, -PaxFromIndia)

# Keep only big airlines
airline_passenger_sums <- df %>%
  group_by(Airline) %>%
  summarise(total_passengers = sum(`Passengers`))
selected_airlines <- airline_passenger_sums %>%
  filter(total_passengers >= 15000000) %>%
  pull(Airline)
df <- df %>%
  filter(Airline %in% selected_airlines)

# Group by year and month
df <- df %>%
  mutate(Date = as.Date(paste(
    paste("20", Year, sep = ""), sprintf("%s", Quarter * 3), "01", sep = "-"
  ))) %>%
  select(Airline, Date, `Passengers`) %>%
  distinct()

# Tidy airline names
df$Airline <- str_to_title(df$Airline)
df$Airline[df$Airline == "Indigo"] <- "IndiGo"
df$Airline[df$Airline == "Spicejet"] <- "SpiceJet"

# Order airlines by their final passenger numbers
airline_order <- df %>%
  group_by(Airline) %>%
  filter(Date == max(Date)) %>%
  arrange(desc(`Passengers`)) %>%
  pull(Airline)

# Set factor levels in reverse order to show top airlines at the top of the legend
df$Airline <- factor(df$Airline, levels = airline_order)

# Determine top N airlines to highlight
N <- 3  # You can change this number
top_airlines <- airline_order[1:N]

# Create a custom color palette with brand colors
n_colors <- length(unique(df$Airline))
print((unique(df$Airline)))
brand_colors <- c(
  "IndiGo" = "#483D8B",
  # Dark slate blue
  "Air India" = "#E00122",
  # Red
  "Air India Express" = "#FF0000",
  # Bright red
  "Emirates Airline" = "#008EEF",
  # Navy blue
  "Etihad Airlines" = "#C8102E",
  # Orange-red
  "Qatar Airways" = "#00B9FF",
  # Light sky blue
  "Air Arabia" = "#FF6600",
  # Orange
  "SpiceJet" = "#FF9900",
  # Orange-yellow
  "Jet Airways" = "#800080"        # Purple
)

# Create a function to generate colors for other airlines
generate_other_colors <- function(n) {
  other_colors <- colorRampPalette(brewer.pal(8, "Set2"))(n)
  setNames(other_colors, setdiff(levels(df$Airline), names(brand_colors)))
}

# Combine brand colors with generated colors for other airlines
color_palette <- c(brand_colors, generate_other_colors(n_colors - length(brand_colors)))

# Create the plot
p <- ggplot(df, aes(
  x = Date,
  y = `Passengers`,
  group = Airline,
  color = Airline
)) +
  geom_line(data = df %>% filter(Airline %in% top_airlines),
            size = 1.2) +
  geom_line(
    data = df %>% filter(!Airline %in% top_airlines),
    alpha = 0.7,
    size = 0.75
  ) +
  ggtitle("International air ridership in India (by carrier)") +
  
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
  
  # Use custom color palette with brand colors
  scale_color_manual(values = color_palette) +
  
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
  labs(x = "Year", y = "Quarterly Passengers (International)", color = "Airline")

# Print the plot
print(p)

# Save the plot with a white background
ggsave(
  "airlines_international.png",
  plot = p,
  width = 12,
  height = 8,
  dpi = 300,
  bg = "white"
)
