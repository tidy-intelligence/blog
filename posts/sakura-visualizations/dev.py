import ibis
from ibis import _
import ibis.selectors as s
from plotnine import *

ibis.options.interactive = True

sakura_first_bloom_dates = ibis.read_csv("data/sakura_first_bloom_dates.csv")
sakura_full_bloom_dates = ibis.read_csv("data/sakura_full_bloom_dates.csv")

first_bloom_long = (sakura_first_bloom_dates
  .drop("30 Year Average 1981-2010", "Notes")
  .rename(location = "Site Name", is_currently_observed = "Currently Being Observed")
  .pivot_longer(s.r["1953":"2023"], names_to = "year", values_to = "first_bloom")
)

full_bloom_long = (sakura_full_bloom_dates
  .drop("30 Year Average 1981-2010", "Notes")
  .rename(location = "Site Name", is_currently_observed = "Currently Being Observed")
  .pivot_longer(s.r["1953":"2023"], names_to = "year", values_to = "full_bloom")
)

sakura_dates = (first_bloom_long.outer_join(full_bloom_long, ["location", "year", "is_currently_observed"])
  .select(~s.contains("_right"))
  .mutate(year = _.year.cast("int32"))
  .mutate(days_to_full_bloom = (_.full_bloom - ibis.date(_.year.cast('string') + '-01-01')).cast('interval("D")').cast("int32"),
          days_from_first_to_full_bloom = _.full_bloom - _.first_bloom)
)

locations_regions = ibis.read_csv("data/locations_region.csv")

southern_islands = ["Naze", "Ishigaki Island", "Miyakojima", "Naha", "Minami Daito Island"]

locations_regions = (locations_regions
  .mutate(
    region = ibis.case().when(_.location.isin(southern_islands), "Ryukyu Islands").else_(_.region).end()
  )
)

sakura_data = (sakura_dates
  .left_join(locations_regions, "location")
  .filter([_.is_currently_observed == True, 
           _.year >= 1954, 
           _.days_to_full_bloom.notnull(),
           _.days_from_first_to_full_bloom.notnull()])
)

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

fpath = "/Library/Fonts/SF-Pro.ttf"

fm.fontManager.addfont(fpath)
prop = fm.FontProperties(fname=fpath)
font_name = prop.get_name()
plt.rcParams["font.family"] = font_name

theme_set(theme_classic(base_size = 16) + theme(figure_size = (12, 8)))

theme_update(
  panel_grid_minor = element_blank(),
  panel_grid_major = element_blank(),
  strip_background = element_blank(),
  axis_title_x = element_blank(),
  axis_title_y = element_blank(),
  axis_ticks = element_blank(),
  axis_line = element_blank()
)

colors = ["#ffb7c5", "#A0522D"]
breaks_year = range(1950, 2031, 20)

sakura_data = sakura_data.to_pandas()

(ggplot(sakura_data, 
         aes(x = "year", y = "days_to_full_bloom"))
  + geom_point(color = colors[0], alpha = 1, size = 4, shape = "o", fill = "white")
  + geom_smooth(method = "loess", se = False,
                color = colors[1], size = 2)
  + facet_wrap("~region", nrow = 1)
  + labs(title = "Day of the year with peak cherry tree blossom for regions in Japan since 1954",
         subtitle = "Cities in northern regions Hokkaidō and Honshū exhibit earlier full blooms, while Ryukyu Islands even later",
         x = None, y = None)
  + scale_x_continuous(breaks = breaks_year)
  + scale_y_continuous(breaks = range(30, 151, 30))
)

