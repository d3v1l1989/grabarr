import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ApolloProvider } from '@apollo/client';
import { Layout, ConfigProvider } from 'antd';
import client from './services/graphql';
import InstanceList from './components/InstanceList';
import InstanceForm from './components/InstanceForm';
import './App.css';

const { Header, Content } = Layout;

const App: React.FC = () => {
  return (
    <ApolloProvider client={client}>
      <ConfigProvider
        theme={{
          token: {
            colorBgBase: '#141414',
            colorTextBase: '#ffffff',
            colorPrimary: '#1890ff',
          },
          components: {
            Layout: {
              bodyBg: '#141414',
              headerBg: '#1f1f1f',
              siderBg: '#1f1f1f',
            },
            Table: {
              colorBgContainer: '#1f1f1f',
              colorText: '#ffffff',
              headerBg: '#1f1f1f',
              rowHoverBg: '#2a2a2a',
            },
            Form: {
              colorText: '#ffffff',
            },
            Input: {
              colorBgContainer: '#1f1f1f',
              colorText: '#ffffff',
            },
          },
        }}
      >
        <Layout className="layout">
          <Header>
            <div className="logo" />
            <h1 style={{ color: 'white' }}>grabarr</h1>
          </Header>
          <Content style={{ padding: '0 50px', marginTop: 64 }}>
            <div className="site-layout-content">
              <Routes>
                <Route path="/" element={<InstanceList />} />
                <Route path="/instances/new" element={<InstanceForm />} />
              </Routes>
            </div>
          </Content>
        </Layout>
      </ConfigProvider>
    </ApolloProvider>
  );
};

export default App; 