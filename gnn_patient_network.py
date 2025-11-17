import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv
from torch_geometric.data import Data
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import networkx as nx
import json

class HealthcareGNN(nn.Module):
    """
    Graph Neural Network for patient readmission prediction
    
    Architecture:
    - 3 Graph Convolutional layers
    - Learns from patient similarity network
    - Predicts readmission risk
    """
    
    def __init__(self, num_features, hidden_dim=64, num_classes=2, dropout=0.3):
        super(HealthcareGNN, self).__init__()
        
        # Graph Convolutional layers
        self.conv1 = GCNConv(num_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, num_classes)
        
        # Dropout for regularization
        self.dropout = dropout
        
    def forward(self, x, edge_index):
        """Forward pass through GNN"""
        
        # First graph convolution + ReLU + Dropout
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Second graph convolution + ReLU + Dropout
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Output layer
        x = self.conv3(x, edge_index)
        
        return F.log_softmax(x, dim=1)


class PatientGraphBuilder:
    """
    Build patient similarity graph from healthcare data
    """
    
    def __init__(self, patients_df):
        self.patients_df = patients_df
        self.scaler = StandardScaler()
        
    def encode_categorical_features(self):
        """Encode categorical features as numeric"""
        
        df = self.patients_df.copy()
        
        # Gender encoding
        df['gender_encoded'] = (df['gender'] == 'Male').astype(int)
        
        # Condition severity encoding
        condition_severity = {
            'None': 0,
            'Allergies': 1,
            'Asthma': 1,
            'Arthritis': 2,
            'Hypertension': 3,
            'Diabetes': 3,
            'Heart Disease': 4
        }
        df['condition_severity'] = df['condition'].map(condition_severity).fillna(0)
        
        # Insurance encoding
        insurance_encoding = {
            'Private': 0,
            'Medicare': 1,
            'Medicaid': 2,
            'Uninsured': 3
        }
        df['insurance_encoded'] = df['insurance'].map(insurance_encoding)
        
        return df
    
    def create_node_features(self):
        """
        Create feature matrix for graph nodes (patients)
        
        Features: age, gender, condition severity, insurance,
                  visits, satisfaction, comorbidity, etc.
        """
        
        df = self.encode_categorical_features()
        
        # Select numerical features
        feature_cols = [
            'age',
            'gender_encoded',
            'condition_severity',
            'insurance_encoded',
            'visitsPerYear',
            'satisfaction',
            'prevAdmissions',
            'comorbidityCount',
            'emergencyRatio',
            'avgLengthOfStay',
            'labAbnormal'
        ]
        
        # Extract features
        features = df[feature_cols].values
        
        # Normalize features
        features_normalized = self.scaler.fit_transform(features)
        
        return torch.FloatTensor(features_normalized)
    
    def create_similarity_edges(self, k_neighbors=5, similarity_threshold=0.5):
        """
        Create edges between similar patients
        
        Similarity based on:
        - Age proximity
        - Same/similar conditions
        - Similar risk profiles
        
        Args:
            k_neighbors: Connect to k most similar patients
            similarity_threshold: Minimum similarity to create edge
        """
        
        df = self.encode_categorical_features()
        
        # Features for similarity calculation
        similarity_features = df[[
            'age', 'condition_severity', 'comorbidityCount',
            'prevAdmissions', 'emergencyRatio'
        ]].values
        
        # Normalize
        similarity_features = StandardScaler().fit_transform(similarity_features)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(similarity_features)
        
        # Create edges
        edges = []
        edge_weights = []
        
        n_patients = len(df)
        
        for i in range(n_patients):
            # Get similarities for patient i
            similarities = similarity_matrix[i]
            
            # Get indices of k most similar patients (excluding self)
            # Set self-similarity to -1 to exclude it
            similarities[i] = -1
            
            # Get top-k similar patients
            top_k_indices = np.argsort(similarities)[-k_neighbors:][::-1]
            
            for j in top_k_indices:
                similarity_score = similarities[j]
                
                # Only create edge if similarity above threshold
                if similarity_score >= similarity_threshold:
                    edges.append([i, j])
                    edge_weights.append(similarity_score)
        
        # Convert to tensor
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        edge_weights = torch.tensor(edge_weights, dtype=torch.float)
        
        print(f"Created graph with {n_patients} nodes and {len(edges)} edges")
        print(f"Average degree: {len(edges) / n_patients:.2f}")
        
        return edge_index, edge_weights
    
    def create_labels(self):
        """Create labels (readmission status)"""
        labels = self.patients_df['readmitted'].astype(int).values
        return torch.LongTensor(labels)
    
    def build_graph(self, k_neighbors=5):
        """
        Build complete PyTorch Geometric graph
        
        Returns:
            Data object containing:
            - x: Node features
            - edge_index: Graph connectivity
            - y: Labels (readmission)
        """
        
        # Create node features
        x = self.create_node_features()
        
        # Create edges
        edge_index, edge_weights = self.create_similarity_edges(k_neighbors)
        
        # Create labels
        y = self.create_labels()
        
        # Create PyTorch Geometric Data object
        data = Data(x=x, edge_index=edge_index, y=y, edge_weight=edge_weights)
        
        print(f"\nGraph Statistics:")
        print(f"  Nodes: {data.num_nodes}")
        print(f"  Edges: {data.num_edges}")
        print(f"  Features per node: {data.num_node_features}")
        print(f"  Positive class: {y.sum().item()} ({y.sum().item()/len(y)*100:.1f}%)")
        
        return data


class GNNTrainer:
    """
    Train and evaluate Graph Neural Network
    """
    
    def __init__(self, model, data, learning_rate=0.01):
        self.model = model
        self.data = data
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=5e-4)
        self.criterion = nn.CrossEntropyLoss()
        
        # Split data into train/val/test
        self.create_splits()
        
    def create_splits(self, train_ratio=0.6, val_ratio=0.2):
        """Create train/validation/test splits"""
        
        n = self.data.num_nodes
        indices = torch.randperm(n)
        
        train_size = int(train_ratio * n)
        val_size = int(val_ratio * n)
        
        self.train_mask = torch.zeros(n, dtype=torch.bool)
        self.val_mask = torch.zeros(n, dtype=torch.bool)
        self.test_mask = torch.zeros(n, dtype=torch.bool)
        
        self.train_mask[indices[:train_size]] = True
        self.val_mask[indices[train_size:train_size + val_size]] = True
        self.test_mask[indices[train_size + val_size:]] = True
        
        print(f"\nData Split:")
        print(f"  Train: {self.train_mask.sum().item()} samples")
        print(f"  Val:   {self.val_mask.sum().item()} samples")
        print(f"  Test:  {self.test_mask.sum().item()} samples")
    
    def train_epoch(self):
        """Train for one epoch"""
        
        self.model.train()
        self.optimizer.zero_grad()
        
        # Forward pass
        out = self.model(self.data.x, self.data.edge_index)
        
        # Calculate loss only on training nodes
        loss = self.criterion(out[self.train_mask], self.data.y[self.train_mask])
        
        # Backward pass
        loss.backward()
        self.optimizer.step()
        
        # Calculate training accuracy
        pred = out[self.train_mask].max(1)[1]
        train_acc = pred.eq(self.data.y[self.train_mask]).sum().item() / self.train_mask.sum().item()
        
        return loss.item(), train_acc
    
    def evaluate(self, mask):
        """Evaluate on given mask (val or test)"""
        
        self.model.eval()
        
        with torch.no_grad():
            out = self.model(self.data.x, self.data.edge_index)
            pred = out[mask].max(1)[1]
            
            # Accuracy
            correct = pred.eq(self.data.y[mask]).sum().item()
            acc = correct / mask.sum().item()
            
            # Precision, Recall, F1
            true_pos = ((pred == 1) & (self.data.y[mask] == 1)).sum().item()
            false_pos = ((pred == 1) & (self.data.y[mask] == 0)).sum().item()
            false_neg = ((pred == 0) & (self.data.y[mask] == 1)).sum().item()
            
            precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
            recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                'accuracy': acc,
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
    
    def train(self, epochs=100, early_stopping_patience=10):
        """
        Train the model
        
        Args:
            epochs: Number of training epochs
            early_stopping_patience: Stop if no improvement for N epochs
        """
        
        print(f"\nTraining GNN for {epochs} epochs...")
        print("=" * 80)
        
        best_val_acc = 0
        patience_counter = 0
        
        for epoch in range(epochs):
            # Train
            loss, train_acc = self.train_epoch()
            
            # Validate
            val_metrics = self.evaluate(self.val_mask)
            
            # Print progress every 10 epochs
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1:3d} | "
                      f"Loss: {loss:.4f} | "
                      f"Train Acc: {train_acc:.4f} | "
                      f"Val Acc: {val_metrics['accuracy']:.4f} | "
                      f"Val F1: {val_metrics['f1']:.4f}")
            
            # Early stopping
            if val_metrics['accuracy'] > best_val_acc:
                best_val_acc = val_metrics['accuracy']
                patience_counter = 0
                # Save best model
                self.best_model_state = self.model.state_dict()
            else:
                patience_counter += 1
                
            if patience_counter >= early_stopping_patience:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break
        
        # Load best model
        self.model.load_state_dict(self.best_model_state)
        
        # Final evaluation
        print("\n" + "=" * 80)
        print("FINAL EVALUATION")
        print("=" * 80)
        
        train_metrics = self.evaluate(self.train_mask)
        val_metrics = self.evaluate(self.val_mask)
        test_metrics = self.evaluate(self.test_mask)
        
        print(f"\nTrain Set:")
        print(f"  Accuracy:  {train_metrics['accuracy']:.4f}")
        print(f"  Precision: {train_metrics['precision']:.4f}")
        print(f"  Recall:    {train_metrics['recall']:.4f}")
        print(f"  F1 Score:  {train_metrics['f1']:.4f}")
        
        print(f"\nValidation Set:")
        print(f"  Accuracy:  {val_metrics['accuracy']:.4f}")
        print(f"  Precision: {val_metrics['precision']:.4f}")
        print(f"  Recall:    {val_metrics['recall']:.4f}")
        print(f"  F1 Score:  {val_metrics['f1']:.4f}")
        
        print(f"\nTest Set:")
        print(f"  Accuracy:  {test_metrics['accuracy']:.4f}")
        print(f"  Precision: {test_metrics['precision']:.4f}")
        print(f"  Recall:    {test_metrics['recall']:.4f}")
        print(f"  F1 Score:  {test_metrics['f1']:.4f}")
        
        return test_metrics
    
    def get_patient_embeddings(self):
        """Get learned patient embeddings from GNN"""
        
        self.model.eval()
        
        with torch.no_grad():
            # Get embeddings from second-to-last layer
            x = self.data.x
            edge_index = self.data.edge_index
            
            # Pass through first two layers
            x = self.model.conv1(x, edge_index)
            x = F.relu(x)
            x = self.model.conv2(x, edge_index)
            
            embeddings = x.numpy()
        
        return embeddings


def visualize_patient_network(data, patients_df, output_file='patient_network.html'):
    """
    Create interactive visualization of patient network
    """
    import networkx as nx
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add nodes
    for i in range(data.num_nodes):
        patient = patients_df.iloc[i]
        G.add_node(i, 
                   patient_id=patient['id'],
                   age=patient['age'],
                   condition=patient['condition'],
                   risk_score=patient['riskScore'],
                   readmitted=patient['readmitted'])
    
    # Add edges
    edge_index = data.edge_index.numpy()
    for i in range(edge_index.shape[1]):
        source, target = edge_index[0, i], edge_index[1, i]
        G.add_edge(int(source), int(target))
    
    # Calculate network statistics
    print(f"\nNetwork Statistics:")
    print(f"  Number of nodes: {G.number_of_nodes()}")
    print(f"  Number of edges: {G.number_of_edges()}")
    print(f"  Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
    print(f"  Network density: {nx.density(G):.4f}")
    
    # Find connected components
    components = list(nx.connected_components(G))
    print(f"  Connected components: {len(components)}")
    print(f"  Largest component size: {len(max(components, key=len))}")
    
    # Save graph structure
    graph_data = {
        'nodes': [{'id': i, **G.nodes[i]} for i in G.nodes()],
        'edges': [{'source': int(u), 'target': int(v)} for u, v in G.edges()],
        'stats': {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes(),
            'density': nx.density(G)
        }
    }
    
    with open('patient_network_data.json', 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"\nNetwork data saved to patient_network_data.json")
    
    return G


# Main execution
if __name__ == "__main__":
    print("=" * 80)
    print("GRAPH NEURAL NETWORK FOR HEALTHCARE ANALYTICS")
    print("=" * 80)
    
    # Load data
    print("\n📊 Loading patient data...")
    patients_df = pd.read_csv('patients.csv')
    
    print(f"Loaded {len(patients_df)} patients")
    
    # Build patient graph
    print("\n🕸️  Building patient similarity network...")
    graph_builder = PatientGraphBuilder(patients_df)
    patient_graph = graph_builder.build_graph(k_neighbors=8)
    
    # Visualize network
    print("\n📈 Analyzing network structure...")
    G = visualize_patient_network(patient_graph, patients_df)
    
    # Create GNN model
    print("\n🤖 Initializing Graph Neural Network...")
    num_features = patient_graph.num_node_features
    model = HealthcareGNN(num_features=num_features, hidden_dim=64, num_classes=2)
    
    print(f"Model architecture:")
    print(f"  Input features: {num_features}")
    print(f"  Hidden dimension: 64")
    print(f"  Output classes: 2 (not readmitted / readmitted)")
    print(f"  Total parameters: {sum(p.numel() for p in model.parameters())}")
    
    # Train model
    print("\n🎓 Training model...")
    trainer = GNNTrainer(model, patient_graph, learning_rate=0.01)
    test_metrics = trainer.train(epochs=100, early_stopping_patience=15)
    
    # Get patient embeddings
    print("\n🔍 Extracting patient embeddings...")
    embeddings = trainer.get_patient_embeddings()
    
    # Save embeddings
    embeddings_df = pd.DataFrame(embeddings)
    embeddings_df['patient_id'] = patients_df['id']
    embeddings_df.to_csv('patient_embeddings_gnn.csv', index=False)
    print(f"Patient embeddings saved to patient_embeddings_gnn.csv")
    
    # Save model
    torch.save(model.state_dict(), 'gnn_model.pt')
    print("Model saved to gnn_model.pt")
    
    # Save metrics
    with open('gnn_metrics.json', 'w') as f:
        json.dump(test_metrics, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ GNN TRAINING COMPLETE!")
    print("=" * 80)
    print(f"\n🎯 Final Test Accuracy: {test_metrics['accuracy']:.2%}")
    print(f"📊 F1 Score: {test_metrics['f1']:.4f}")
    print("\nGenerated files:")
    print("  - gnn_model.pt (trained model)")
    print("  - patient_embeddings_gnn.csv (learned patient representations)")
    print("  - patient_network_data.json (graph structure)")
    print("  - gnn_metrics.json (performance metrics)")