import React from 'react';
import { useQuery, gql } from '@apollo/client';
import { Table, Button, Space, Tag } from 'antd';
import { Link } from 'react-router-dom';

const GET_INSTANCES = gql`
  query GetInstances {
    sonarrInstances {
      id
      name
      url
      isActive
      status
      lastChecked
      errorMessage
    }
  }
`;

const InstanceList: React.FC = () => {
  const { loading, error, data } = useQuery(GET_INSTANCES);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Link to={`/instances/${record.id}`}>{text}</Link>
      ),
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'default';
        if (status === 'online') color = 'success';
        if (status === 'offline') color = 'error';
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: 'Last Checked',
      dataIndex: 'lastChecked',
      key: 'lastChecked',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button type="primary" size="small">
            Edit
          </Button>
          <Button danger size="small">
            Delete
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Link to="/instances/new">
          <Button type="primary">
            Add New Instance
          </Button>
        </Link>
      </div>
      <Table
        columns={columns}
        dataSource={data.sonarrInstances}
        rowKey="id"
      />
    </div>
  );
};

export default InstanceList; 