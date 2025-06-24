# vectorize_courses.py
from sentence_transformers import SentenceTransformer

# 1. Load the pre-trained 'all-MiniLM-L6-v2' model
# The first time you run this, it will download the model weights (approx. 90MB)
# This might take a moment depending on your internet connection.
print("Loading Sentence-BERT model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully.")

# Your example course description
course_description = "This course is a detailed study of the compilation process. Topics include interpreters, overall design implementation of a compiler, techniques for parsing, building and manipulating intermediate representations of a program, implementation of important features, code generation and optimization."

# 2. Encode the course description to get its vector embedding
print(f"\nEncoding description: '{course_description[:80]}...'")
embedding = model.encode(course_description)

# 3. Print the embedding and its shape
print(f"Embedding generated. Shape: {embedding.shape}")
print(f"First 10 dimensions of the embedding: {embedding[:10]}")

# You can encode multiple sentences at once
other_descriptions = [
    "An introduction to data structures and algorithms.",
    "Advanced topics in machine learning and neural networks.",
    "A course focusing on operating system design and concurrent programming."
]

print("\nEncoding multiple descriptions...")
embeddings_batch = model.encode(other_descriptions)
print(f"Batch embeddings shape: {embeddings_batch.shape}")
print(f"Embedding for the second course (first 10 dimensions): {embeddings_batch[1][:10]}")

# For semantic similarity, you can use the model's utility function
from sentence_transformers import util
query_embedding = model.encode("courses about programming languages")
similarities = util.cos_sim(query_embedding, embeddings_batch)
print(f"\nSimilarity to 'courses about programming languages':")
for i, desc in enumerate(other_descriptions):
    print(f"- '{desc[:50]}...': {similarities[0][i].item():.4f}")