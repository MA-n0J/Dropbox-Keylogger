import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog
from PyQt5.QtCore import Qt
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from gensim import corpora
from gensim.models import LdaModel
from gensim.models import CoherenceModel
import matplotlib.pyplot as plt
import nltk


try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download('stopwords')

# Define these globally
dictionary = None
best_num_topics = None


def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    return tokens

def prepare_for_lda(texts):
    global dictionary  # Declare as global
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    return dictionary, corpus

def compute_coherence_values(dictionary, corpus, texts, num_topics_range):
    coherence_values = []
    for num_topics in num_topics_range:
        lda_model = LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=15)
        coherence_model = CoherenceModel(model=lda_model, texts=texts, dictionary=dictionary, coherence='c_v')
        coherence_values.append(coherence_model.get_coherence())
    return coherence_values

def interpret_topics(lda_model):
    topics = lda_model.print_topics(num_words=5)
    result = ""
    for topic_num, topic in topics:
        words = [word.split("*")[1].strip(' "') for word in topic.split(" + ")]
        result += f"Topic {topic_num}: {' | '.join(words)}\n"
    return result

class LdaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.textbox = QTextEdit(self)
        self.textbox.setPlaceholderText("Enter text here")
        layout.addWidget(self.textbox)

        self.browse_button = QPushButton('Browse File', self)
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_button)

        self.result_display = QTextEdit(self)
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        self.process_button = QPushButton('Process Text', self)
        self.process_button.clicked.connect(self.process_text)
        layout.addWidget(self.process_button)

        self.setLayout(layout)
        self.setWindowTitle('LDA Topic Model')
        self.setGeometry(100, 100, 600, 400)
        self.show()

    def browse_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filePath, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt);;All Files (*)", options=options)

        if filePath:
            with open(filePath, 'r') as file:
                text = file.read()
                self.textbox.setPlainText(text)

    def process_text(self):
        global best_num_topics  # Declare as global
        input_text = self.textbox.toPlainText()

        # Preprocess the text data
        texts = [preprocess_text(input_text)]

        # Prepare for LDA
        dictionary, corpus = prepare_for_lda(texts)

        # Define the range of num_topics for tuning
        num_topics_range = range(2, 11)

        # Compute coherence values
        coherence_values = compute_coherence_values(dictionary, corpus, texts, num_topics_range)

        # Choose the optimal num_topics
        best_num_topics = num_topics_range[coherence_values.index(max(coherence_values))]

        # Visualize coherence scores
        plt.plot(num_topics_range, coherence_values)
        plt.xlabel("Number of Topics")
        plt.ylabel("Coherence Score")
        plt.title("Optimal Number of Topics")
        plt.show()

        # Train the final LDA model
        final_lda_model = LdaModel(corpus, num_topics=best_num_topics, id2word=dictionary, passes=15)

        # Interpret topics and update result_display
        result = interpret_topics(final_lda_model)
        self.result_display.setPlainText(result)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            filePath = url.toLocalFile()
            if filePath.endswith('.txt'):
                with open(filePath, 'r') as file:
                    text = file.read()
                    self.textbox.setPlainText(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LdaApp()
    sys.exit(app.exec_())
