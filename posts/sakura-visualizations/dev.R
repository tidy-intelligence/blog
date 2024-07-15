library(dplyr)
library(tidyr)
library(readr)
library(lubridate)
library(ggplot2)

sakura_first_bloom_dates <- read_csv("data/sakura_first_bloom_dates.csv") 
sakura_full_bloom_dates <- read_csv("data/sakura_full_bloom_dates.csv")
  
first_bloom_long <- sakura_first_bloom_dates |>
  select(-`30 Year Average 1981-2010`, -Notes) |>
  rename(location = `Site Name`, is_currently_observed = `Currently Being Observed`) |>
  pivot_longer(`1953`:`2023`, names_to = "year", values_to = "first_bloom")

full_bloom_long <- sakura_full_bloom_dates |>
  select(-`30 Year Average 1981-2010`, -Notes) |>
  rename(location = `Site Name`, is_currently_observed = `Currently Being Observed`) |>
  pivot_longer(`1953`:`2023`, names_to = "year", values_to = "full_bloom")

sakura_dates <- first_bloom_long |>
  full_join(full_bloom_long, c("location", "year", "is_currently_observed")) |>
  mutate(year = as.integer(year),
         days_to_full_bloom = as.integer(full_bloom - as.Date(paste(year, "-01-01", sep = ""))),
         days_from_first_to_full_bloom = as.integer(full_bloom - first_bloom))

locations_regions <- read_csv("data/locations_region.csv") 

southern_islands <- c("Naze", "Ishigaki Island", "Miyakojima", "Naha", "Minami Daito Island")

locations_regions <- locations_regions |> 
  mutate(region = if_else(location %in% southern_islands, "Ryukyu Islands", region))

sakura_data <- sakura_dates |> 
  left_join(locations_regions, join_by(location)) |> 
  filter(is_currently_observed == TRUE &
          year >= 1954 &
          !is.na(days_to_full_bloom) & 
          !is.na(days_from_first_to_full_bloom))

sakura_data <- sakura_data |> 
  mutate(region = factor(region, levels = c("Hokkaidō", "Honshū", "Kyūshū", "Shikoku", "Ryukyu Islands")))

theme_set(theme_classic(base_size = 16, base_family = "SF Pro")) 

theme_update(
  panel.grid.minor = element_blank(),
  panel.grid.major = element_blank(),
  strip.text = element_text(size = 16),
  strip.background = element_blank(),
  axis.title.x = element_blank(), 
  axis.title.y = element_blank()
)

colors <- c("#ffb7c5", "#A0522D")
breaks_year <- seq(1950, 2030, by = 20)

sakura_data |> 
  ggplot(aes(x = year, y = days_to_full_bloom)) +
  geom_point(color = colors[1], alpha = 0.9, size = 4, shape = 21, fill = "white") +
  geom_smooth(method = loess, se = FALSE,
              color = colors[2], linewidth = 1) +
  facet_wrap(~region, nrow = 1) + 
  labs(title = "Day of the year with peak cherry tree blossom for regions in Japan since 1953",
       subtitle = "Cities in northern regions Hokkaidō and Honshū exhibit earlier full blooms, while Ryukyu Islands even later",
       x = NULL, y = NULL) +
  scale_x_continuous(breaks = breaks_year) +
  scale_y_continuous(breaks = seq(30, 150, by = 30)) +
  theme(legend.position = "none")
