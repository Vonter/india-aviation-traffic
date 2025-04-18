# Load required libraries
library(circlize)
library(readr)
library(dplyr)
library(wesanderson)  # For Wes Anderson color palettes

options(scipen = 999)

# Read the CSV file
df <- read_csv("../aggregated/domestic/city.csv")

# Prepare the data for the chord diagram
# We'll use the total passenger flow between cities
chord_data <- df %>%
  group_by(City1, City2) %>%
  summarise(TotalPax = sum(PaxToCity2 + PaxFromCity2)) %>%
  ungroup() %>%
  # Filter for pairs with more than 15 million passengers
  filter(TotalPax > 15e6)

print(chord_data)

# Create a matrix from the data
cities <- unique(c(chord_data$City1, chord_data$City2))
n_cities <- length(cities)
matrix_data <- matrix(0, nrow = n_cities, ncol = n_cities)
rownames(matrix_data) <- colnames(matrix_data) <- cities

for (i in 1:nrow(chord_data)) {
  row <- which(cities == chord_data$City1[i])
  col <- which(cities == chord_data$City2[i])
  matrix_data[row, col] <- chord_data$TotalPax[i]
}

# Set up colors using Wes Anderson palette
# We'll use the "Zissou1" palette and repeat colors if needed
zissou_colors <- wes_palette("Zissou1", n_cities, type = "continuous")

print(matrix_data)

# Set up colors for the diagram
colors <- rainbow(n_cities)

# Custom function to format numbers
format_number <- function(x) {
  ifelse(x >= 1e9, paste0(round(x / 1e9, 1), "B"), ifelse(x >= 1e6, paste0(round(x /
                                                                                   1e6, 1), "M"), comma(x)))
}

# Function to create the chord diagram
create_chord_diagram <- function() {
  circos.clear()
  par(mar = rep(2, 4),
      cex = 0.7,
      bg = "#F0F0F0")  # Set background color
  circos.par(
    start.degree = 90,
    gap.degree = 2,
    track.margin = c(-0.1, 0.1),
    points.overflow.warning = FALSE
  )
  
  chordDiagram(
    matrix_data,
    grid.col = colors,
    directional = 1,
    direction.type = c("diffHeight", "arrows"),
    link.arr.type = "big.arrow",
    link.sort = TRUE,
    link.largest.ontop = TRUE,
    annotationTrack = "grid",
    preAllocateTracks = 1,
    link.visible = matrix_data > 0,
    link.border = "#F0F0F0",
    # Set link border color
    link.lwd = 0.5,
    # Set link border width
    grid.border = "#404040"  # Set grid border color
  )
  
  # Add city labels
  circos.track(
    track.index = 1,
    track.height = 2,
    panel.fun = function(x, y) {
      circos.text(
        CELL_META$xcenter,
        CELL_META$ylim[1],
        CELL_META$sector.index,
        facing = "clockwise",
        niceFacing = TRUE,
        adj = c(0, 0.5),
        cex = 0.8,
        ,
        col = "#404040"
      )
    },
    bg.border = NA
  )
  
  # Add total passenger flow labels
  circos.track(
    track.index = 2,
    panel.fun = function(x, y) {
      sector.name = CELL_META$sector.index
      xlim = CELL_META$xlim
      ylim = CELL_META$ylim
      total_flow = sum(matrix_data[sector.name, ]) + sum(matrix_data[, sector.name])
      circos.text(
        mean(xlim),
        mean(ylim),
        format_number(total_flow),
        cex = 0.5,
        niceFacing = TRUE
      )
    },
    bg.border = NA
  )
  
  title("City pairs with cumulative ridership above 15 million (2015-2025)",
        cex.main = 1)
}

# Create the chord diagram and save as PNG
png(
  "passenger_flows.png",
  width = 1200,
  height = 1200,
  units = "px",
  res = 300
)
create_chord_diagram()
dev.off()
