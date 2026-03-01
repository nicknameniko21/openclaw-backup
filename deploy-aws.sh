#!/bin/bash
# Deploy to AWS EC2 Free Tier
# t2.micro: 750 hours/month free

REGION="us-east-1"
INSTANCE_TYPE="t2.micro"
AMI="ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS
KEY_NAME="kimi-claw-key"
SECURITY_GROUP="kimi-claw-sg"

echo "Deploying to AWS EC2..."

# Create key pair if not exists
aws ec2 describe-key-pairs --key-names $KEY_NAME 2>/dev/null || {
    echo "Creating key pair..."
    aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text > ~/.ssh/$KEY_NAME.pem
    chmod 400 ~/.ssh/$KEY_NAME.pem
}

# Create security group
aws ec2 describe-security-groups --group-names $SECURITY_GROUP 2>/dev/null || {
    echo "Creating security group..."
    aws ec2 create-security-group --group-name $SECURITY_GROUP --description "Kimi Claw automation"
    aws ec2 authorize-security-group-ingress --group-name $SECURITY_GROUP --protocol tcp --port 22 --cidr 0.0.0.0/0
}

# Launch instance
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-groups $SECURITY_GROUP \
    --user-data file://aws-user-data.sh \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance launched: $INSTANCE_ID"

# Wait for instance
echo "Waiting for instance to be ready..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "Instance IP: $PUBLIC_IP"

# Save to config
echo "ec2:$PUBLIC_IP" >> /root/.openclaw/workspace/.orchestrator/aws-instances.txt

echo "✓ AWS deployment complete"
echo "Connect: ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
