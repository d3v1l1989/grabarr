import { gql } from '@apollo/client';

export const LOGIN = gql`
  mutation Login($username: String!, $password: String!) {
    login(username: $username, password: $password) {
      message
    }
  }
`;

export const LOGOUT = gql`
  mutation Logout {
    logout {
      message
    }
  }
`; 