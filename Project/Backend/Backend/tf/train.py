import pandas as pd
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

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

# Veriyi eğitim ve test setlerine bölmek
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

# Keras modeli oluşturma
input_layer = Input(shape=(X.shape[1],))
dense_1 = Dense(128, activation='relu')(input_layer)
dense_2 = Dense(64, activation='relu')(dense_1)
output_layer = Dense(len(label_encoder.classes_), activation='softmax')(dense_2)  # Çıkış katmanı, sınıf sayısına göre ayarlandı
model = Model(inputs=input_layer, outputs=output_layer)

# Modeli derleme
model.compile(optimizer=Adam(), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

model.fit(X_train, y_train, epochs=100, validation_data=(X_test, y_test))

# Modeli kaydetme
save_dir = os.path.join(current_dir, 'saved_models')
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
existing_models = os.listdir(save_dir)
model_name = f'saved_model_{len(existing_models) + 1}.h5'
save_path = os.path.join(save_dir, model_name)
model.save(save_path)

print(f"Model başarıyla kaydedildi")
