import pandas as pd
d1  = pd.read_csv(r"C:\Users\ADIL TRADERS\Desktop\spotify\SpotifyHybridRecommender\Data\content_base_data\filter_content.csv")
d2  =  pd.read_csv(r"C:\Users\ADIL TRADERS\Desktop\spotify\SpotifyHybridRecommender\Data\filtered_data.csv")
print(d1.shape) # 5000
print(d2.shape )# 3000
      
# d1 is large have all songs , d2 has not all songs d2 is subset of d1 . we have seen an issue on song creep of radiohead 
# dask as gab categorize krte hen to wo lexical order m sort

# score normlazing to reduve weigh bias towards collbaraive as it is sparse so sim score small value compare to content
# W1 x norm_content + W2 x norm_collab





