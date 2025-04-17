import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import config from '../config';

const httpLink = createHttpLink({
  uri: `${config.apiUrl}/graphql`,
  credentials: 'include', // This is important for cookies
});

const authLink = setContext((_, { headers }) => {
  return {
    headers: {
      ...headers,
    }
  };
});

const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
  credentials: 'include', // This is important for cookies
});

export default client; 