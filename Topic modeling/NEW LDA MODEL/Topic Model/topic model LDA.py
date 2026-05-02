import random
import numpy as np
import pandas as pd
import os.path
from IPython.display import display
from nltk.corpus import stopwords
from tqdm import tqdm
from collections import Counter
import ast
from gensim import corpora
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import seaborn as sb
import csv
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob
import scipy.stats as stats
import pyLDAvis
from sklearn.decomposition import TruncatedSVD
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.manifold import TSNE
import nltk
from nltk import pos_tag, RegexpTokenizer, PorterStemmer
from nltk.tokenize import word_tokenize


nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

from bokeh.plotting import figure, output_file, show
from bokeh.models import Label
from bokeh.io import output_notebook
output_notebook()


def load_data(path,file_name):
    """
    Input  : path and file_name
    Purpose: loading text file
    Output : list of paragraphs/documents and
             title(initial 100 words considred as title of document)
    """
    documents_list = []
    titles=[]
    with open( os.path.join(path, file_name) ,"r") as fin:
        for line in fin.readlines():
            text = line.strip()
            documents_list.append(text)
    print("Total Number of Documents:",len(documents_list))
    titles.append( text[0:min(len(text),100)] )
    return documents_list,titles
def preprocess_data(doc_set):
    """
    Input  : docuemnt list
    Purpose: preprocess text (tokenize, removing stopwords, and stemming)
    Output : preprocessed text
    """
    # initialize regex tokenizer
    tokenizer = RegexpTokenizer(r'\w+')
    # create English stop words list
    en_stop = set(stopwords.words('english'))
    # Create p_stemmer of class PorterStemmer
    p_stemmer = PorterStemmer()
    # list for tokenized documents in loop
    texts = []
    # loop through document list
    for i in doc_set:
        # clean and tokenize document string
        raw = i.lower()
        tokens = tokenizer.tokenize(raw)
        # stem tokens
        stemmed_tokens = [p_stemmer.stem(i) for i in tokens]
        # add tokens to list
        texts.append(stemmed_tokens)
    return texts


def prepare_corpus(doc_clean):
    """
    Input  : clean document
    Purpose: create term dictionary of our corpus and Converting list of documents (corpus) into Document Term Matrix
    Output : term dictionary and Document Term Matrix
    """
    # Creating the term dictionary of our courpus, where every unique term is assigned an index. dictionary = corpora.Dictionary(doc_clean)
    dictionary = corpora.Dictionary(doc_clean)
    # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
    return dictionary,doc_term_matrix


def change_matrix(doc_clean):
    dictionary, doc_term_matrix = prepare_corpus(doc_clean)
    # Get the number of unique terms (size of the vocabulary)
    small_count_vectorizer = len(dictionary)
    # Initialize a dense matrix of zeros (documents x terms)
    small_document_term_matrix = np.zeros((len(doc_term_matrix), small_count_vectorizer), dtype=int)
    # Fill the dense matrix with term frequencies
    for doc_idx, doc in enumerate(doc_term_matrix):
        for term_id, freq in doc:
            small_document_term_matrix[doc_idx, term_id] = freq

    # Print the dense Document-Term Matrix
    return small_count_vectorizer,small_document_term_matrix

def get_keys(topic_matrix):
    '''
    returns an integer list of predicted topic
    categories for a given topic matrix
    '''
    keys = topic_matrix.argmax(axis=1).tolist()
    return keys

def keys_to_counts(keys):
    '''
    returns a tuple of topic categories and their
    accompanying magnitudes for a given list of keys
    '''
    count_pairs = Counter(keys).items()
    categories = [pair[0] for pair in count_pairs]
    counts = [pair[1] for pair in count_pairs]
    return (categories, counts)


#

# Define helper functions
def get_top_n_words(n, keys, document_term_matrix, count_vectorizer):
    '''
    returns a list of n_topic strings, where each string contains the n most common
    words in a predicted category, in order
    '''
    top_word_indices = []
    for topic in range(n_topics):
        temp_vector_sum = 0
        for i in range(len(keys)):
            if keys[i] == topic:
                temp_vector_sum += document_term_matrix[i]
        temp_vector_sum = temp_vector_sum.toarray()
        top_n_word_indices = np.flip(np.argsort(temp_vector_sum)[0][-n:],0)
        top_word_indices.append(top_n_word_indices)
    top_words = []
    for topic in top_word_indices:
        topic_words = []
        for index in topic:
            temp_word_vector = np.zeros((1,document_term_matrix.shape[1]))
            temp_word_vector[:,index] = 1
            the_word = count_vectorizer.inverse_transform(temp_word_vector)[0][0]
            topic_words.append(the_word.encode('ascii','ignore').decode('utf-8'))
        top_words.append(" ".join(topic_words))
    return top_words


#Define helper functions
def get_mean_topic_vectors(keys, two_dim_vectors):
    '''
    returns a list of centroid vectors from each predicted topic category
    '''
    mean_topic_vectors = []
    for t in range(n_topics):
        articles_in_that_topic = []
        for i in range(len(keys)):
            if keys[i] == t:
                articles_in_that_topic.append(two_dim_vectors[i])

        articles_in_that_topic = np.vstack(articles_in_that_topic)
        mean_article_in_that_topic = np.mean(articles_in_that_topic, axis=0)
        mean_topic_vectors.append(mean_article_in_that_topic)
    return mean_topic_vectors



alltext = pd.read_csv('/Users/jianing/PycharmProjects/PythonProject2/topicmodeling/Alltext.csv',delimiter=',',engine='python')
# Combine all columns into one column
alltext_single_column = alltext.melt(value_name="Combined")["Combined"].dropna().reset_index(drop=True)
small_count_vectorizer = CountVectorizer(stop_words='english', max_features=40000)
small_text_sample = alltext_single_column.values

print('Reviews before vectorization: {}'.format(small_text_sample[123]))

small_document_term_matrix = small_count_vectorizer.fit_transform(small_text_sample)
print('Reviews after vectorization: \n{}'.format(small_document_term_matrix[123]))

#because we need 10 topics
n_topics = 7

lda_model = LatentDirichletAllocation(n_components=n_topics, learning_method='online',
                                          random_state=0, verbose=0)

# Fit the LDA model on the document-term matrix
lda_model.fit(small_document_term_matrix)

# 1) doc_topic_dists: (n_docs × n_topics)
doc_topic_dists = lda_model.transform(small_document_term_matrix)
# ensure each row sums to 1
doc_topic_dists = doc_topic_dists / doc_topic_dists.sum(axis=1, keepdims=True)

# 2) topic_term_dists: (n_topics × n_terms)
# lda_model.components_ has shape (n_topics × n_terms), but not normalized
topic_term_dists = lda_model.components_
topic_term_dists = topic_term_dists / topic_term_dists.sum(axis=1)[:, np.newaxis]

# 3) doc_lengths: one entry per document
# for a CSR matrix .sum(axis=1) returns a column vector; .A1 flattens to 1-D
doc_lengths = small_document_term_matrix.sum(axis=1).A1

# 4) vocab: list of all feature names in the same order as columns of the DTM
vocab = small_count_vectorizer.get_feature_names_out()

# 5) term_frequencies: total count of each term across all docs
term_frequencies = small_document_term_matrix.sum(axis=0).A1




# Prepare visualization

vis_data = pyLDAvis.prepare(
    topic_term_dists=topic_term_dists,
    doc_topic_dists=doc_topic_dists,
    doc_lengths=doc_lengths,
    vocab=vocab,
    term_frequency=term_frequencies
)
pyLDAvis.save_html(vis_data, 'lda_interactive.html')

# Save to HTML
pyLDAvis.save_html(vis_data, 'lda_interactive.html')

