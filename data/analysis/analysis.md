
[dataset] profiles: 322

[age]
  missing: 0
  count:   322
  min:     18
  max:     70
  mean:    33.65
  median:  33.00
  by age group:
age
18-25    42
26-30    72
31-35    99
36-40    64
41+      45

[gender]
gender
male         213
female        96
fnb            4
nonbinary      4
nbm            3
fmnb           1
mnb            1

[interested in]
  missing/unknown: 3
  interested in male: 119
  interested in female: 229
  interested in both male+female: 29
  interested in nonbinary: 51

  top interest combinations:
interestedIn
female                     179
male                        81
female, nonbinary           21
female, male, nonbinary     19
male, nonbinary              9
female, male                 7
unknown                      3
male, female, nonbinary      2
male, female                 1

[location]
  top 15 (raw strings):
location
San Francisco Bay Area    56
NYC                       19
Central Europe            14
London                    13
London UK                  9
UK                         9
DC                         9
Flexible                   7
North America              7
Los Angeles                7
Boston                     5
Austin                     4
Berlin                     4
Asia                       4
North America Flexible     4

  top 15 (last token heuristic):
location
Area            59
NYC             23
UK              19
Flexible        16
Europe          15
London          14
DC              11
Angeles          9
America          8
Philadelphia     8
Asia             8
Boston           6
Chicago          6
Berlin           6
Austin           6

[location flexibility]
locationFlexibility
high       145
some       131
none        30
unknown     16

[done] demographics summary printed.



_____________________________________________


[text coverage]
  profiles with any text: 322 / 322

[summary stats] (profiles with text)
  word_count: mean=973.304 | median=724.000 | min=102.000 | max=12720.000
  avg_sentence_len_words: mean=23.176 | median=19.141 | min=7.536 | max=144.000
  exclam_per_100_words: mean=0.492 | median=0.317 | min=0.000 | max=3.679
  emoji_per_100_words: mean=0.408 | median=0.000 | min=0.000 | max=8.350
  questions_per_100_words: mean=0.286 | median=0.130 | min=0.000 | max=1.954

[done]

_____________________________________________

 ax.boxplot(data2, labels=genders2, showfliers=True)

[charts]
  wrote: data/charts/graph_a_age_patterns.png
  wrote: data/charts/graph_b_exclam_by_gender.png
  wrote: data/charts/graph_c_location_flex.png

[tfidf] distinctive vocabulary tables
  gender counts (with text): {'male': 213, 'female': 96, 'fnb': 4, 'nonbinary': 4, 'nbm': 3, 'fmnb': 1, 'mnb': 1}


  [women vs men] top distinctive terms (women)
        term    score
        love 0.017635
         man 0.009953
        eyes 0.009282
         men 0.009001
        life 0.008462
       ready 0.008290
        girl 0.007719
      korean 0.007542
      nature 0.007328
 looking man 0.007051
      abroad 0.006788
       dream 0.006752
   community 0.006604
      divide 0.006532
      living 0.006504
      female 0.006246
   nurturing 0.006157
     browser 0.006089
communicator 0.005961
   love love 0.005953
      values 0.005923
      edited 0.005893
 emotionally 0.005737
       green 0.005659
      humour 0.005581

  [women vs men] top distinctive terms (men)
     term    score
    think 0.013213
     like 0.012394
   things 0.010155
      i'm 0.009334
     i've 0.009048
       ll 0.009035
    games 0.008620
      com 0.008290
 software 0.007976
   people 0.007569
 research 0.007460
    https 0.007384
    ideas 0.007348
       ve 0.007103
   really 0.006825
    don't 0.006742
     good 0.006519
     male 0.006476
effective 0.006447
     blog 0.006300
  twitter 0.006235
   pretty 0.006142
     it's 0.006117
     make 0.006045
    board 0.005955

  saved: data/analysis/tables/tfidf_women_over_men.csv
  saved: data/analysis/tables/tfidf_men_over_women.csv

  age cohort counts (with text): {'millennials': 220, 'gen_z': 80, 'gen_x': 22}

  [age cohort: millennials] top distinctive terms
     term    score
     kids 0.009533
   person 0.008749
  partner 0.007977
      let 0.007942
     life 0.007703
     make 0.006626
  profile 0.006513
effective 0.006414
    going 0.006400
     home 0.006296
    share 0.006217
    means 0.006108
      nyc 0.005887
     want 0.005842
     best 0.005578
  support 0.005545
    wants 0.005517
       ll 0.005439
 partners 0.005428
  looking 0.005407
  saved: data/analysis/tables/tfidf_age_millennials.csv

  [age cohort: gen_z] top distinctive terms
         term    score
          alt 0.016755
        think 0.013354
         love 0.009869
      believe 0.008884
          try 0.008800
     software 0.007744
        india 0.007711
         kind 0.007638
     date doc 0.007476
        moral 0.007449
   interested 0.007074
 occasionally 0.006799
          doc 0.006601
     document 0.006600
 getting know 0.006524
relationships 0.006488
       people 0.006441
     stanford 0.006412
     solution 0.006406
         haha 0.006258
  saved: data/analysis/tables/tfidf_age_gen_z.csv

  [age cohort: gen_x] top distinctive terms
            term    score
         phoenix 0.020231
        football 0.020043
           sales 0.018415
          denver 0.018067
             log 0.017134
            join 0.016954
family community 0.016893
     uc berkeley 0.016850
         retired 0.016673
  social justice 0.016247
          improv 0.016136
              uc 0.016090
            sign 0.016089
             i'm 0.015894
       community 0.015814
           sober 0.015743
 service privacy 0.015584
      pittsburgh 0.015293
   terms service 0.014894
            bike 0.014729
  saved: data/analysis/tables/tfidf_age_gen_x.csv

  region groups eligible (>= 20 profiles): ['Area', 'NYC']

  [region: Area] top distinctive terms
         term    score
          san 0.026088
    francisco 0.023174
san francisco 0.023150
          bay 0.017301
           ai 0.016451
     berkeley 0.016165
           sf 0.015951
    anonymous 0.014924
           pm 0.014476
     research 0.014430
     bay area 0.011951
           ve 0.011598
          jun 0.009978
     partners 0.009251
         yash 0.009236
      excited 0.009159
      dropbox 0.008534
           uc 0.008512
      attuned 0.008425
         area 0.008398
  saved: data/analysis/tables/tfidf_region_Area.csv

  [region: NYC] top distinctive terms
      term    score
       alt 0.046083
       nyc 0.031069
    domain 0.026253
     think 0.024188
      like 0.019695
  date doc 0.017746
       buy 0.016033
     don't 0.015967
      city 0.014662
      want 0.014290
      free 0.014192
    nathan 0.013457
   website 0.013401
thoughtful 0.013107
      skip 0.013032
  new york 0.012927
      york 0.012927
      date 0.012866
 york city 0.012570
subscribed 0.012500
  saved: data/analysis/tables/tfidf_region_NYC.csv

[done]