import pandas as pd
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import load_model
import numpy as np

def predict(name):
        print(name)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dataset_path = os.path.join(current_dir, 'datasets', 'processed_youtube.csv')
        df = pd.read_csv(dataset_path)

        # Gerekli sütunları seçme
        X = df[['year', 'runtime', 'favorability_rounded', 'positive', 'neutral', 'negative',
                'rating_normalized', 'country_normalized', 'genre_normalized']]
        y = df['name']

        # Veriyi normalize etme
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Film isimlerini sayısal etiketlere dönüştürme
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)

        # Veriyi eğitim ve test setlerine bölmek (burada eğitim seti kullanılmış gibi varsayalım)
        X_train, _, y_train, _ = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

        # En son kaydedilmiş modeli yükleme
        saved_models_dir = os.path.join(current_dir, 'saved_models')
        latest_model_path = max([os.path.join(saved_models_dir, f) for f in os.listdir(saved_models_dir)], key=os.path.getctime)
        model = load_model(latest_model_path)

        # Veriyi modele uygun hale getirme
        input_data = X_scaled[df[df['name'] == name].index]
        predicted_vector = model.predict(input_data)

        top_indices = np.argsort(predicted_vector[0])[::-1][:5]
        top_films = label_encoder.inverse_transform(top_indices)
        return top_films
