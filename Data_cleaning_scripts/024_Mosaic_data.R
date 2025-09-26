# Mosaic data cleaning script
# Created:    2024-09-24
# Auhtors:    Christian Vedel [christian-vs@sam.sdu.dk],
#
# Purpose:    Mosaic data cleaning
#
# Output:     Clean tmp version of the data

# ==== Libraries =====
library(tidyverse)
source("Data_cleaning_scripts/000_Functions.R")
library(foreach)
library(readxl)


# ==== Read data ====
tmp_funky = function(x) x$occhisco %>% unique()
dirs = list.dirs("Data/Raw_data/2509_New_data/Mosaic", full.names = FALSE)
data0 = foreach(d = dirs, .combine = "bind_rows") %do% {
    d_full = paste0("Data/Raw_data/2509_New_data/Mosaic/", d)
    files = list.files(d_full, full.names = TRUE, pattern = "\\_codes.csv$")
    files_labels = list.files(d_full, full.names = TRUE, pattern = "\\_labels.csv$")
    if(length(files)>1) stop("More than one file in folder")
    if(length(files_labels)>1) stop("More than one label file in folder")
    if(length(files)==0) return(NULL) # Skip folders with no data

    data0 = read_csv2(files) %>%
        select(year, relateor, occupat, occhisco) %>%
        mutate(
            source = d
        )

    if(tmp_funky(data0) %>% length() < 10){
        cat("\nLess than 10 unique HISCO codes in", d)
        return(NULL) # Skip folders with no data
    }

    labels = read_csv2(files_labels)

    data0$country = labels$country

    return(data0)
}

# ==== Cleaning data0 ====
data1 = data0 %>% 
  rename(
    occ1 = occupat,
    hisco_1 = occhisco
  ) %>% 
  select(occ1, hisco_1, country, source)

data2 = data0 %>% # Vesion with relateor added in the occ string
    mutate(
        occ1 = paste(relateor, occupat, sep = " ")
    ) %>%
    rename(
        hisco_1 = occhisco
    ) %>% 
    select(occ1, hisco_1, country, source)

data1 = bind_rows(data1, data2)

# ==== More cleaning ====
data1 = data1 %>% 
  mutate(
    hisco_1 = as.numeric(hisco_1),
  ) %>% 
  mutate(
    hisco_1 = ifelse(is.na(hisco_1), -1, hisco_1)
  )

data1 = data1 %>%
  mutate(
    hisco_2 = " ",
    hisco_3 = " ",
    hisco_4 = " ",
    hisco_5 = " "
  )

# ==== Country to lang ====
# [1] "Albania"   "France"    "Germany"   "Belarus"   "Poland"    "Lithuania"
# [7] "Serbia"    "Turkey"

data1 = data1 %>% 
    mutate(
        lang = case_when(
            country == "Albania" ~ "sq",
            country == "France" ~ "fr",
            country == "Germany" ~ "ge",
            country == "Belarus" ~ "be",
            country == "Poland" ~ "pl",
            country == "Lithuania" ~ "lt",
            country == "Serbia" ~ "sr",
            country == "Turkey" ~ "tr",
            TRUE ~ "unk"
        )
    )

# ==== Cross walk ====
# Key
# Everything with no exact equivalent in standard HISCO is filtered off

cross_walk = read_csv("Data/Raw_data/O-clack/n2h_2.csv")
key = cross_walk %>%
  # Remove anything with a note
  filter(is.na(comments)) %>% 
  filter(napp.eq.hisco == 1) %>% 
  # Only when we are completely sure of agreement
  filter(hisco.code.num == napp.code.num)

key0 = read_csv("Data/Key.csv")

all_data = data1 %>% 
  semi_join(key, by = c("hisco_1"="hisco.code.num"))

# ==== Get combinations by source ====

set.seed(20)
sources = unique(all_data$source)
all_data = foreach(s = sources, .combine = "bind_rows") %do% {
  cat("\nGetting combinations for", s)
  data_s = all_data %>% filter(source == s) %>% mutate_all(as.character)
  n_s = NROW(data_s)
  n_comb = min(50000, n_s*2) # Max 50k combinations or double the data size
  combinations = data_s %>% 
    mutate_all(as.character) %>%
    filter(hisco_2 == " ", hisco_1 != "-1") %>% 
    sample_n(n_comb, replace = TRUE) %>% 
    Combinations("")

  data_s = data_s %>% bind_rows(combinations) 
  return(data_s)
}

# Remove cases with 2 of the same occupation
all_data = all_data %>% 
  filter(hisco_1 != hisco_2)

# ==== Check against authoritative HISCO list ====
load("Data/Key.Rdata")

key = key %>% select(hisco, code)

# Remove data not in key (erronoeous data somehow)
all_data %>% 
  filter(!hisco_1 %in% key$hisco)

n1 = NROW(all_data)
all_data = all_data %>% 
  filter(hisco_1 %in% key$hisco) %>% 
  filter(hisco_2 %in% key$hisco) %>% 
  filter(hisco_3 %in% key$hisco) %>% 
  filter(hisco_4 %in% key$hisco) %>% 
  filter(hisco_5 %in% key$hisco)

NROW(all_data) - n1 # 0 observations

# Turn into character
all_data = all_data %>% 
  mutate_all(as.character)

# Add code
all_data = all_data %>% 
  left_join(
    key, by = c("hisco_1" = "hisco")
  ) %>% 
  rename(code1 = code) %>% 
  left_join(
    key, by = c("hisco_2" = "hisco")
  ) %>% 
  rename(code2 = code) %>% 
  left_join(
    key, by = c("hisco_3" = "hisco")
  ) %>% 
  rename(code3 = code) %>% 
  left_join(
    key, by = c("hisco_4" = "hisco")
  ) %>% 
  rename(code4 = code) %>% 
  left_join(
    key, by = c("hisco_5" = "hisco")
  ) %>% 
  rename(code5 = code)

# Add RowID 
all_data = all_data %>% 
  ungroup() %>% 
  mutate(RowID = 1:n())

# ==== Save ====
save(all_data, file = "Data/Tmp_data/Mosaic_data.Rdata")

