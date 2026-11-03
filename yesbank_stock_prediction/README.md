# YES Bank Monthly Closing Price Prediction

This project uses the supplied monthly YES Bank OHLC dataset to predict the **following month's closing price**. It is an educational time-series regression example, not investment advice.

## Why the target is shifted

For each month, the model uses that month's open, high, low, close, recent closing-price history, and calendar fields to predict the next month's close. This means the model does not use the target month's high/low/close as input. All features are available after the current month has ended.

The data contains 185 monthly records from July 2005 through November 2020. It does not contain news, market indices, or company fundamentals, so it cannot isolate the effect of any specific event mentioned in the accompanying project brief.

## Models and evaluation

The training script compares:

- A persistence baseline: next month's close equals this month's close.
- Ridge regression with standardization and time-series cross-validation for alpha selection.
- Random Forest regression with time-series cross-validation for tree settings.

The final 20% of observations are held out chronologically. Model-family selection uses cross-validation on the earlier training period; the holdout is reserved for final reporting. Metrics include MAE, RMSE, MAPE, and R². A model is not considered useful merely because it beats a constant or random baseline; compare it with the persistence baseline and interpret errors in the context of the stock's volatility.

On this dataset's holdout period (December 2017–November 2020), the persistence baseline achieved an MAE of 23.80, compared with 30.58 for Random Forest and 31.74 for Ridge. Although Ridge had the lowest cross-validation MAE in the earlier training period and is saved as the final model, neither trained model beat the simple baseline on the holdout. The large errors reflect how difficult this series is to forecast from OHLC history alone.

## Run

```bash
python -m pip install -r requirements.txt
python train.py --data data/data_YesBank_StockPrices.csv
```

The script writes `artifacts/metrics.json`, `artifacts/test_predictions.csv`, `artifacts/actual_vs_predicted.png`, and `artifacts/best_model.joblib`. The model artifact is fitted on all available rows after evaluation, ready for the next one-month-ahead prediction. Since the dataset ends in November 2020, that forecast is for December 2020 and should not be interpreted as a current-market forecast.

## Dataset fields

`Date`, `Open`, `High`, `Low`, and `Close` are monthly records. The source deck contains a mislabeled description for `Close`; this project treats it as the closing stock price, consistent with the column name and project objective.
