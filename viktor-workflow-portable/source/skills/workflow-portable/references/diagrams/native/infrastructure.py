"""Original synthetic example; review/install dependencies separately; not run here."""
from diagrams import Diagram, Cluster
from diagrams.generic.blank import Blank

with Diagram("Synthetic infrastructure", show=False, outformat="svg"):
    ingress = Blank("Ingress")
    with Cluster("Application boundary"):
        api = Blank("API")
        queue = Blank("Queue")
        worker = Blank("Worker")
    store = Blank("Owned store")
    ingress >> api >> queue >> worker
    api >> store
    worker >> store
