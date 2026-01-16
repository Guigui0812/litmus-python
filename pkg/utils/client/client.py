import os, boto3
from kubernetes import client, config, dynamic
from kubernetes.client import api_client
import pkg.aws_az.types.types as experimentDetails
from botocore.config import Config
import pkg.aws_az.environment.environment as experimentEnv

# Client Class is maintaining clients for k8s
class K8sClient(object):
    def __init__(self, conf=None):
        self.clientCoreV1   =  client.CoreV1Api(conf)
        self.clientDyn      =  dynamic.DynamicClient(api_client.ApiClient(configuration=conf))
        self.clientApps     =  client.AppsV1Api(conf)

# AWSClient is maintaining clients for aws
class AWSClient(object):
    def __init__(self, experimentsDetails):

        self.clientElb =  boto3.client('elb', region_name=experimentsDetails.AWSRegion)
        self.clientElbv2 =  boto3.client('elbv2', region_name=experimentsDetails.AWSRegion)

# Config maintain configuration for in and out cluster
class Configuration(object):

    def __init__(self, kubeconfig=None, configurations=None):
        self.kubeconfig    = kubeconfig
        self.configurations =  configurations
    
    # get_config return the configuration
    def get_config(self):

        global configs
        if self.kubeconfig != "":
            configs = self.kubeconfig
        elif os.getenv('KUBERNETES_SERVICE_HOST'):
            configs = config.load_incluster_config()
        else:
            configs = config.load_kube_config()

        self.configurations = configs
        return configs
