'''
This script makes class_infos more balanced.
'''
import os
import argparse
import pickle
import one_hot
from random import shuffle
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt

outputs_dir = 'outputs'
train_out_dir = os.path.join(outputs_dir, 'train')
test_out_dir = os.path.join(outputs_dir, 'test')

ap = argparse.ArgumentParser()
ap.add_argument('-b', '--box_size', required=True, help="Specify a length of square box side.")
ap.add_argument('-ub', '--upper_bound', required=False, help="Specify the upper bound which essentially is the eventual distribution of each class after balance.")
args = vars(ap.parse_args())

box_size = int(args.get('box_size'))
# Balance ratio
b_ratio = 1.0
batch_size = 32

# Load data
with open(os.path.join(train_out_dir, 'train.pickle'), 'rb') as data:
    train = pickle.load(data)
with open(os.path.join(test_out_dir, 'test.pickle'), 'rb') as data:
    test = pickle.load(data)

print('Training set size:', len(train))
print('Testing set size:', len(test))

# Initialize keras image generator
datagen = ImageDataGenerator(rotation_range=10, shear_range=0.1)

# Load all class_infos that were extracted
classes = [label.strip() for label in list(open('classes.txt', 'r'))]
class_infos = [{'class': class_name, 'occurrences': 0} for class_name in classes]

for train_sample in train:
    label = one_hot.decode(train_sample['label'], classes)
    # Find index of this label in class_infos list
    class_idx = classes.index(label)
    # Update the number of occurrences
    class_infos[class_idx]['occurrences'] += 1

# Sort class_infos by occurrences
class_infos = sorted(class_infos, key=lambda class_info: class_info['occurrences'], reverse=True)
if not args.get('upper_bound'):
    max_occurances = class_infos[0]['occurrences']
else:
    max_occurances = int(args.get('upper_bound'))

min_occurances = class_infos[len(class_infos)-1]['occurrences']
for class_info in class_infos:
    class_info['deviation'] = max_occurances - class_info['occurrences']

print('====================== Distribution of classes ======================')
for label in class_infos:
    print('CLASS: {}; occurrences: {}; deviation: {}'.format(label['class'], label['occurrences'], label['deviation']))
print('Max occurrences:', max_occurances)
print('Min occurrences:', min_occurances)
print('=====================================================================')

for class_info in class_infos:
    # Get one_hot representation of current class
    hot_class = one_hot.encode(class_info['class'], classes)
    # Calculate how many new samples have to be generated
    how_many_gen = int(round(class_info['deviation'] * b_ratio))
    print('\nClass: {}; How many new samples to generate: {}'.format(class_info['class'], how_many_gen))
    # Create images and labels for data representing current class
    images = np.asarray([train_rec['features'].reshape((box_size, box_size, 1)) for train_rec in train if np.array_equal(train_rec['label'], hot_class)])
    labels = np.tile(hot_class, reps=(class_info['occurrences'], 1))

    # Generate new images
    # datagen.fit(images)
    new_data = []
    for X_batch, y_batch in datagen.flow(images, labels, batch_size=batch_size):
        # # Plot newly generated images
        # n_cols = 4
        # n_rows = int(np.ceil(len(X_batch) / 4))
        # figure, axis_arr = plt.subplots(n_rows, n_cols, figsize=(12, 4))
        # for row in range(n_rows):
        #     for col in range(n_cols):
        #         axis_arr[row, col].imshow(X_batch[row*n_cols + col].reshape((box_size, box_size)), cmap='gray')
        #         # Remove explicit axises
        #         # axis_arr[row, col].axis('off')
        # plt.show()

        # If enough samples were generated
        if len(new_data) >= how_many_gen:
            break;
        for idx in range(len(X_batch)):
            new_record = {'features': X_batch[idx].flatten(), 'label': y_batch[idx]}
            new_data.append(new_record)

    print('CLASS: {}; NEW records: {};'.format(class_info['class'], len(new_data)))
    # Append newly generated data & shuffle given dataset
    train += new_data

# Shuffle sets
print('\nShuffling training set ...')
shuffle(train)

print('\nNEW Training set size:', len(train))

with open(os.path.join(train_out_dir, 'train.pickle'), 'wb') as f:
    pickle.dump(train, f, protocol=pickle.HIGHEST_PROTOCOL)
    print('Training data has been successfully dumped into', f.name)
with open(os.path.join(test_out_dir, 'test.pickle'), 'wb') as f:
    pickle.dump(test, f, protocol=pickle.HIGHEST_PROTOCOL)
    print('Testing data has been successfully dumped into', f.name)

print('\n\n# Like our facebook page @ https://www.facebook.com/mathocr/')
