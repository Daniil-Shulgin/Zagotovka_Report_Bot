import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import io
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ID = '1qisfDBdQVu7UTjtZrAo0M5s3ZLZyVrp_ohZMKFv9sb0'
CSV_URL = f'https://docs.google.com/spreadsheets/d/{ID}/export?format=csv'
SHEET_GID = 1232882650 
CSV_22_25_URL = f'https://docs.google.com/spreadsheets/d/{ID}/export?format=csv&gid={SHEET_GID}&single=true'
ROWS = 53
COLUMN_25 = [0, 1, 4, 5, 6, 9]
COLUMN_22_25 = [12, 13, 14, 15, 16]
COLUMNS_22_25 = ['2022', '2023', '2024', '2025']

# --- ФУНКЦИЯ ЗАГРУЗКИ И ПРЕДВАРИТЕЛЬНОЙ ОБРАБОТКИ ДАННЫХ ---

def load_and_prepare_data():
    """Загружает данные из Google Sheets и выполняет их обработку."""
    try:
        logging.info("Начало загрузки данных из Google Sheets...")
        
        buy_stat_df = pd.read_csv(CSV_URL, nrows=ROWS, usecols=COLUMN_25, na_values=['N/A', 'NA', '-', 'None', ''])
        buy_stat_22_25_df = pd.read_csv(CSV_22_25_URL, nrows=ROWS, usecols=COLUMN_22_25)

        new_cols = ['delta_date', 'week', 'Safonov', 'Grushin', 'Katishev', 'total_for_week']
        buy_stat_df.columns = new_cols
        buy_stat_df_new = buy_stat_df.iloc[1:].reset_index(drop=True)
        buy_stat_df_new['date'] = buy_stat_df_new['delta_date'].astype(str).str[-8:]
        buy_stat_df_new['date'] = pd.to_datetime(buy_stat_df_new['date'], format='%d.%m.%y')

        int_cols = ['week', 'Safonov', 'Grushin', 'Katishev', 'total_for_week']
        for col in int_cols:
            if col in buy_stat_df_new.columns:
                buy_stat_df_new[col] = pd.to_numeric(buy_stat_df_new[col], errors='coerce').astype('Int16')
            else:
                logging.warning(f"Столбец '{col}' не найден в buy_stat_df_new.")
                
        new_cols_22_25 = ['week', '2025', '2024', '2023', '2022']
        buy_stat_22_25_df.columns = new_cols_22_25
        buy_stat_22_25_df = buy_stat_22_25_df.drop([0,1], axis=0).reset_index(drop=True)
        buy_stat_22_25_df['week'] = pd.to_numeric(buy_stat_22_25_df['week'], errors='coerce').astype('Int16')

        for col in COLUMNS_22_25:
            if col in buy_stat_22_25_df.columns:
                buy_stat_22_25_df[col] = buy_stat_22_25_df[col].astype(str).str.strip().str.replace(',', '.', regex=False)
                numeric_series = pd.to_numeric(buy_stat_22_25_df[col], errors='coerce')
                buy_stat_22_25_df[col] = numeric_series.round(0).astype('Int16')
            else:
                logging.warning(f"Столбец '{col}' не найден в buy_stat_22_25_df.")

        logging.info("Данные успешно загружены и предобработаны.")
        return buy_stat_df_new, buy_stat_22_25_df

    except Exception as e:
        error_msg = f"Критическая ошибка при загрузке или обработке данных: {e}"
        logging.error(error_msg)
        return None, error_msg

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ АНАЛИЗА ---

# График для кнопки [report_week]
def chart(df_new, pr_w):
    """Строит график общей заготовки за текущий год."""
    try:
        fig, ax = plt.subplots(figsize=(10, 10))
        df_new.loc[:pr_w, ['date', 'total_for_week']].plot(
            x='date', 
            y='total_for_week', 
            ax=ax, 
            marker='o', 
            color='#0d0dde',
            lw=3,
            legend=False
        )

        ax.set_title('Общая заготовка зерна с начала 2025', fontsize=24, fontweight='bold', pad=20)
        ax.set_ylabel('Объем(тонн)', fontsize=20)
        ax.set_xlabel('Месяц', fontsize=20)
        ax.tick_params(axis='both', labelsize=15)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close(fig)
        buffer.seek(0)
        
        logging.info("График успешно создан и сохранен в буфер в памяти.")
        
        return buffer.getvalue() 
    except Exception as e:
        logging.error(f"Ошибка при генерации или сохранении графика: {e}")
        return str(e)

# Расчет метрик для кнопки [report_week]
def metrics(df_new):
    """Считает основные метрики для отчета за неделю."""
    current_week = datetime.now().isocalendar()[1]
    trg_w = current_week - 1 
    pr_w = trg_w - 1
    
    try:
        total_for_week_median = df_new['total_for_week'].median()

        trg_w_mask = df_new['week'] == trg_w
        pr_w_mask = df_new['week'] == pr_w

        if not df_new.loc[trg_w_mask].empty and not df_new.loc[pr_w_mask].empty:
            
            Safonov_trg_w = df_new.loc[trg_w_mask, 'Safonov'].iloc[0]
            Safonov_pr_w = df_new.loc[pr_w_mask, 'Safonov'].iloc[0]
            Safonov_delta = Safonov_trg_w - Safonov_pr_w

            Grushin_trg_w = df_new.loc[trg_w_mask, 'Grushin'].iloc[0]
            Grushin_pr_w = df_new.loc[pr_w_mask, 'Grushin'].iloc[0]
            Grushin_delta = Grushin_trg_w - Grushin_pr_w

            Katishev_trg_w = df_new.loc[trg_w_mask, 'Katishev'].iloc[0]
            Katishev_pr_w = df_new.loc[pr_w_mask, 'Katishev'].iloc[0]
            Katishev_delta = Katishev_trg_w - Katishev_pr_w

            ttl_trg_w = df_new.loc[trg_w_mask, 'total_for_week'].iloc[0]
            ttl_pr_w = df_new.loc[pr_w_mask, 'total_for_week'].iloc[0]
            
            total_delta_median = ttl_trg_w - total_for_week_median
            total_delta_prev = ttl_trg_w - ttl_pr_w
            
            current_date = df_new.loc[trg_w_mask, 'date'].iloc[0].strftime('%d.%m.%Y')
            current_delta_date = df_new.loc[trg_w_mask, 'delta_date'].iloc[0]
            
            return {
                'trg_w': trg_w,
                'pr_w': pr_w,
                'current_delta_date': current_delta_date,
                'current_date': current_date,
                'Safonov_trg_w': Safonov_trg_w,
                'Safonov_delta': Safonov_delta,
                'Grushin_trg_w': Grushin_trg_w,
                'Grushin_delta': Grushin_delta,
                'Katishev_trg_w': Katishev_trg_w,
                'Katishev_delta': Katishev_delta,
                'ttl_trg_w': ttl_trg_w,
                'ttl_pr_w': ttl_pr_w,
                'total_delta_median': total_delta_median,
                'total_delta_prev': total_delta_prev
            }
        else:
            raise IndexError(f"Нет данных за целевую неделю ({trg_w}) или предыдущую ({pr_w}).")

    except Exception as e:
        logging.error(f"Ошибка при расчете метрик: {e}")
        return str(e)

# --- ГЛАВНЫЕ ФУНКЦИИ БОТА ---

# Обработка кнопки [report_week]   

def report_week():
    """Считает основные метрики и строит график за этот год."""
    buy_stat_df_new, _ = load_and_prepare_data()

    if buy_stat_df_new is None:
        return {"error": _}

    metrics_data = metrics(buy_stat_df_new)
    
    if isinstance(metrics_data, str):
        return {"error": f"Ошибка метрик: {metrics_data}"}

    pr_w = metrics_data.get('pr_w')
    chart_bytes = chart(buy_stat_df_new, pr_w)
    
    if isinstance(chart_bytes, str):
        return {"error": f"Ошибка графика: {chart_bytes}"}
    
    logging.info("Недельный отчет успешно создан.")
    return {'chart_bytes': chart_bytes, 'metrics': metrics_data}

# Обработка кнопки [compare_year_report]   

def compare_year_report():
    """Строит график сравнения по годам."""
    _, buy_stat_22_25_df = load_and_prepare_data()

    if _ is None:
        return {"error": buy_stat_22_25_df}

    for col in COLUMNS_22_25:
        if col in buy_stat_22_25_df.columns:
            buy_stat_22_25_df[col] = buy_stat_22_25_df[col].rolling(window=3).mean()      
            buy_stat_22_25_df[col] = buy_stat_22_25_df[col].rolling(window=4).mean()      
        else:
            print(f"ВНИМАНИЕ: Столбец '{col}' не найден в DataFrame и пропущен.")
    
    try:
        fig, ax = plt.subplots(figsize=(10, 10))

        line_widths = [1, 2, 3, 4]
        colors = ['#c8c8e6', '#9898d9', '#6464d1', '#0d0dde']

        for i, col in enumerate(COLUMNS_22_25):
            ax.plot(
                buy_stat_22_25_df['week'],
                buy_stat_22_25_df[col],
                label=col,
                marker='o',
                linewidth=line_widths[i],
                color=colors[i]
            )

        ax.legend(
            title='Год',
            fontsize='large',
            title_fontsize='x-large',
            loc='upper left',
            frameon=True,
            shadow=True
        )

        ax.set_title('Сравнение общей заготовки (2022-2025)', fontsize=24, fontweight='bold', pad=20)
        ax.set_xlabel('Неделя', fontsize=20)
        ax.set_ylabel('Объем(тонн)', fontsize=20)
        ax.tick_params(axis='both', labelsize=15)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close(fig)
        buffer.seek(0)
        
        logging.info("График успешно создан и сохранен в буфер в памяти.")
        
        return buffer.getvalue() 
    except Exception as e:
        logging.error(f"Ошибка при генерации или сохранении графика: {e}")
        return str(e)