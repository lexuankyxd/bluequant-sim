# BlueQuant-alpha-tools
BlueQuant alpha tools

# Requirements
+ Python
+ Matplotlib

# PNL Summary
Print summary of a pnl file, only one alpha at a time
```
python3 pnl_summary.py pnl/alpha1
```
The output will be like
```
   START-     END    LONG  SHORT      PNL    TVR   RET     IR
20220101-20221231   500.0  500.0    513.2   36.6  50.1  0.084
20230101-20231231   500.0  500.0    394.3   34.8  38.5  0.055
20240101-20240720   500.0  500.0    599.3   33.6 105.6  0.080

20220101-20240720   500.0  500.0   1506.8   35.2  57.6  0.068
```

# Plot PNL
Plot pnl chart of alphas, can plot multiple alphas in one graph
```
python3 pnl_plot.py pnl/alpha1 pnl/alpha2 pnl/alpha3
```
The graph is like below
![Figure_1](https://github.com/user-attachments/assets/3450e777-a006-4dbb-a21c-ccd070049dad)
