import React, { useState } from 'react';
import { Form, Input, Button, message, Space, Typography } from 'antd';
import { useMutation, gql } from '@apollo/client';

const { Text } = Typography;

const CREATE_INSTANCE = gql`
  mutation CreateInstance($input: SonarrInstanceInput!) {
    createSonarrInstance(input: $input) {
      id
      name
      url
      status
    }
  }
`;

const TEST_CONNECTION = gql`
  mutation TestConnection($input: ConnectionTestInput!) {
    testConnection(input: $input) {
      status
      version
      appName
      isProduction
      error
    }
  }
`;

interface InstanceFormProps {
  onSuccess?: () => void;
}

const InstanceForm: React.FC<InstanceFormProps> = ({ onSuccess }) => {
  const [form] = Form.useForm();
  const [createInstance] = useMutation(CREATE_INSTANCE);
  const [testConnection] = useMutation(TEST_CONNECTION);
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields(['url', 'apiKey']);
      setTesting(true);
      const result = await testConnection({
        variables: {
          input: {
            url: values.url,
            apiKey: values.apiKey,
          },
        },
      });
      setTestResult(result.data.testConnection);
      if (result.data.testConnection.status === 'online') {
        message.success('Connection successful!');
      } else {
        message.error('Connection failed: ' + result.data.testConnection.error);
      }
    } catch (error) {
      message.error('Failed to test connection');
      console.error(error);
    } finally {
      setTesting(false);
    }
  };

  const onFinish = async (values: any) => {
    try {
      await createInstance({
        variables: {
          input: {
            name: values.name,
            url: values.url,
            api_key: values.apiKey,
          },
        },
      });
      message.success('Instance created successfully');
      form.resetFields();
      if (onSuccess) onSuccess();
    } catch (error) {
      message.error('Failed to create instance');
      console.error(error);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      style={{ maxWidth: 600 }}
    >
      <Form.Item
        name="name"
        label="Instance Name"
        rules={[{ required: true, message: 'Please input the instance name!' }]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        name="url"
        label="Sonarr URL"
        rules={[
          { required: true, message: 'Please input the Sonarr URL!' },
          { type: 'url', message: 'Please enter a valid URL!' },
        ]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        name="apiKey"
        label="API Key"
        rules={[{ required: true, message: 'Please input the API key!' }]}
      >
        <Input.Password />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button 
            type="primary" 
            onClick={handleTestConnection}
            loading={testing}
          >
            Test Connection
          </Button>
          <Button type="primary" htmlType="submit">
            Create Instance
          </Button>
        </Space>
      </Form.Item>

      {testResult && (
        <Form.Item>
          <Text type={testResult.status === 'online' ? 'success' : 'danger'}>
            Status: {testResult.status}
            {testResult.version && ` | Version: ${testResult.version}`}
            {testResult.error && ` | Error: ${testResult.error}`}
          </Text>
        </Form.Item>
      )}
    </Form>
  );
};

export default InstanceForm; 