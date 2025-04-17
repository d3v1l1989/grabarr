import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ApolloProvider } from '@apollo/client';
import { Layout } from 'antd';
import { client } from './services/graphql';
import InstanceList from './components/InstanceList';
import InstanceForm from './components/InstanceForm';
import './App.css';

const { Header, Content } = Layout;

const App: React.FC = () => {
  return (
    <ApolloProvider client={client}>
      <Router>
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
      </Router>
    </ApolloProvider>
  );
};

export default App; 