import json
import pandas as pd
"""
Тестовые функции, не имеют отношения к проекту, потом будут удалены
"""
def retrieve_payment_status(df: pd.DataFrame, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'status': df[df.transaction_id == transaction_id].payment_status.item()})
    return json.dumps({'error': 'transaction id not found.'})

def retrieve_payment_date(df: pd.DataFrame, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'date': df[df.transaction_id == transaction_id].payment_date.item()})
    return json.dumps({'error': 'transaction id not found.'})