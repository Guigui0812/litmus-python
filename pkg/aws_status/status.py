from distutils.log import error
from re import subn
import boto3, logging
import pkg.utils.client.client as client

# AWS_AZ class is checking the status of LoadBalancer and availablity zone
class AWS_AZ(object):
    def __init__(self, client=None):
        self.clients = client

    # CheckAWSStatus checks target load balancer availability
    def CheckAWSStatus(self, experimentsDetails):
        
        self.clients = client.AWSClient(experimentsDetails).clientElb
        
        if experimentsDetails.LoadBalancerName == "" or experimentsDetails.LoadBalancerZones == "" :
            return ValueError("Provided LoadBalancer Name or LoadBalancerZoner are empty")
        
        try:
            self.clients.describe_load_balancers()['LoadBalancerDescriptions']
        except Exception as exp:
            return ValueError(exp)
        logging.info("[Info]: LoadBalancer and Availablity of zone has been checked")

    def getSubnetFromVPC(self, experimentsDetails): 
        
        if experimentsDetails.LoadBalancerVersion == "elb":
        
            client = boto3.client('elb', region_name=experimentsDetails.AWSRegion)
            try:
                response = client.describe_load_balancers(
                    LoadBalancerNames=[
                        experimentsDetails.LoadBalancerName,
                    ]
                )
                return (response['LoadBalancerDescriptions'][0]['Subnets'])
            except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
                return ValueError(exp)
        
        # Use dedicated client for elv2 when env var has been set
        elif experimentsDetails.LoadBalancerVersion == "elbv2":

            client = boto3.client('elbv2', region_name=experimentsDetails.AWSRegion)
            try:
                response = client.describe_load_balancers(
                    Names=[
                        experimentsDetails.LoadBalancerName,
                    ]
                )
                return (response['LoadBalancers'][0]['AvailabilityZones'])
            except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
                return ValueError(exp)

    def getTargetSubnet(self, experimentsDetails, zone):
        client = boto3.client('ec2', region_name=experimentsDetails.AWSRegion)
        if experimentsDetails.LoadBalancerVersion == "elb":
            
            try:
                lst=self.getSubnetFromVPC(experimentsDetails)
                i=0
                for i in range(len(lst)):
                    response = client.describe_subnets(
                        SubnetIds=[
                            lst[i],
                        ],
                    )
                    if(response['Subnets'][0]['AvailabilityZone']) == zone:
                        return lst[i], None
            except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
                return lst[i], ValueError(exp)
            
        # Specific section to deal with the output of the elv2 client
        elif experimentsDetails.LoadBalancerVersion == "elbv2":
            try:
                lst =self.getSubnetFromVPC(experimentsDetails)
                i=0
                for i in range(len(lst)):
                    if (lst[i]['ZoneName']) == zone:
                        return lst[i]['SubnetId'], None
            except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
                return lst[i], ValueError(exp)
                
    def detachSubnet(self, experimentsDetails, subnet): 
        client = boto3.client('elb', region_name=experimentsDetails.AWSRegion)
        try:
                response = client.detach_load_balancer_from_subnets(
                LoadBalancerName=experimentsDetails.LoadBalancerName,
                Subnets=subnet
            )
                if (response['ResponseMetadata']['HTTPStatusCode']) != "200":
                    ValueError("[Error]: Fail to detach the target subnet %s", subnet)
        except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
            return ValueError(exp)

    # Specific method to detach the subnet with elbv2 client
    def detachSubnetv2(self, experimentsDetails, subnet): 
        client = boto3.client('elbv2', region_name=experimentsDetails.AWSRegion)
        try:
            
            subnetsToKeep = []
            response = client.describe_load_balancers(
                    Names=[
                        experimentsDetails.LoadBalancerName,
                    ]
                )
            
            # List subnet to keep that are currently attached to the LB
            for az in response['LoadBalancers'][0]['AvailabilityZones']:
                if az['SubnetId'] not in subnet:
                    subnetsToKeep.append(az['SubnetId'])
            if experimentsDetails.Sequence is "parallel":
                response = client.set_subnets(
                    LoadBalancerArn=response['LoadBalancers'][0]['LoadBalancerArn'],
                    Subnets=[""]
                )
            else:
                response = client.set_subnets(
                    LoadBalancerArn=response['LoadBalancers'][0]['LoadBalancerArn'],
                    Subnets=subnetsToKeep
                )
                        
        except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
            return ValueError(exp)

    def attachSubnet(self, experimentsDetails, subnet): 
        client = boto3.client('elb', region_name=experimentsDetails.AWSRegion)
        try:
                response = client.attach_load_balancer_to_subnets(
                LoadBalancerName=experimentsDetails.LoadBalancerName,
                Subnets=subnet
            )
                if (response['ResponseMetadata']['HTTPStatusCode']) != "200":
                    ValueError("[Error]: Fail to attach the target subnet %s", subnet)
        except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
            return ValueError(exp)
    
    # Specific method to attach the removed subnet with elbv2 client after Chaos
    def attachSubnetv2(self, experimentsDetails, subnet):
        client = boto3.client('elbv2', region_name=experimentsDetails.AWSRegion)
        try:
            
            subnetsToKeep = [subnet]
            response = client.describe_load_balancers(
                    Names=[
                        experimentsDetails.LoadBalancerName,
                    ]
                )
            
            for az in response['LoadBalancers'][0]['AvailabilityZones']:
                if az['SubnetId'] not in subnet:
                    subnetsToKeep.append(az['SubnetId'])

            response = client.set_subnets(
                LoadBalancerArn=response['LoadBalancers'][0]['LoadBalancerArn'],
                Subnets=subnetsToKeep
            )
                        
        except (self.clients.exceptions.AccessPointNotFoundException, self.clients.exceptions.InvalidConfigurationRequestException) as exp:
            return ValueError(exp)
