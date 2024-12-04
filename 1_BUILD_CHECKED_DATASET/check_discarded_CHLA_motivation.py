import pandas as pd 

df    = pd.read_csv("/g100_work/OGS_devC/camadio/GLOBIO/Globio/1_BUILD_CHECKED_DATASET/discarded_CHLA.csv")
serv  = df.file_name.drop_duplicates()
df1   = df.loc[serv.index]
df1.groupby(by="motivation").count()

serv2 = df[df.motivation=="pres_none"]
df3   = df[df.file_name==serv2.file_name]  


