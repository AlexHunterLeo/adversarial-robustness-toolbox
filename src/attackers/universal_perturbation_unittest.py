import unittest

import keras.backend as k
import tensorflow as tf

from src.attackers.universal_perturbation import UniversalPerturbation
from src.classifiers.cnn import CNN
from src.utils import load_mnist, get_labels_np_array


class TestUniversalPerturbation(unittest.TestCase):

    def test_mnist(self):
        session = tf.Session()
        k.set_session(session)

        comp_params = {"loss": 'categorical_crossentropy',
                       "optimizer": 'adam',
                       "metrics": ['accuracy']}

        # get MNIST
        batch_size, nb_train, nb_test = 10, 10, 10
        (X_train, Y_train), (X_test, Y_test) = load_mnist()
        X_train, Y_train = X_train[:nb_train], Y_train[:nb_train]
        X_test, Y_test = X_test[:nb_test], Y_test[:nb_test]
        im_shape = X_train[0].shape

        # get classifier
        classifier = CNN(im_shape, act="relu")
        classifier.compile(comp_params)
        classifier.fit(X_train, Y_train, epochs=1, batch_size=batch_size, verbose=0)
        scores = classifier.evaluate(X_test, Y_test)
        print("\naccuracy on test set: %.2f%%" % (scores[1] * 100))

        attack_params = {"verbose": 0,
                         "clip_min": 0.,
                         "clip_max": 1.,
                         "attacker": "deepfool"}

        attack = UniversalPerturbation(classifier.model, session, attacker_params={"max_iter":50})
        x_train_adv = attack.generate(X_train, **attack_params)
        self.assertTrue((attack.fooling_rate >= 0.2) or not attack.converged)

        x_test_adv = X_test + attack.v

        self.assertFalse((X_test == x_test_adv).all())

        train_y_pred = get_labels_np_array(classifier.predict(x_train_adv))
        test_y_pred = get_labels_np_array(classifier.predict(x_test_adv))

        self.assertFalse((Y_test == test_y_pred).all())
        self.assertFalse((Y_train == train_y_pred).all())

        scores = classifier.evaluate(x_train_adv, Y_train)
        print('\naccuracy on adversarial train examples: %.2f%%' % (scores[1] * 100))

        scores = classifier.evaluate(x_test_adv, Y_test)
        print('\naccuracy on adversarial test examples: %.2f%%' % (scores[1] * 100))

if __name__ == '__main__':
    unittest.main()
